"""
Custom traffic simulation engine — deliberately NOT SUMO/TraCI.

Method
------
Each intersection approach is modeled with a deterministic (shockwave)
queueing model, the same class of model behind Webster's signal-delay
formula:

    - demand(t)   : time-varying arrival rate over the 3-hour peak window,
                    a single-hump profile scaled by peak_volume_veh_hr.
    - capacity(t) : lanes * saturation_flow_per_lane * (green_s / cycle_s)
    - queue(t+dt) = max(0, queue(t) + arrivals(t) - departures(t))
    - departures  = min(queue(t) + arrivals(t), capacity(t))
    - delay       : Little's Law, W = L / lambda, applied per step and
                    averaged (time-weighted) across the window.

Two control strategies are evaluated over the same demand:

    baseline  - fixed-time signal plan, no rerouting.
    proposed  - each step, an ML congestion classifier
                (app/ml_engine.py) scores the approach; when it predicts
                HIGH congestion, the engine (a) extends green time toward
                max_green_s, bounded by the cycle, and (b) diverts a
                fraction of arriving demand to the least-saturated
                neighboring node with spare capacity — this is the
                "uneven distribution" correction: load is shifted away
                from the bottleneck toward under-utilized corridor
                capacity instead of just being served in place.

This produces genuine, reproducible before/after metrics (delay, queue,
throughput, travel time, degree of saturation) for the 09:00-12:00 and
16:00-19:00 windows without requiring a SUMO installation.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    from backend.app.network_data import NODES, TIME_WINDOWS, AVG_VEHICLE_SPACING_M, NodeConfig
    from backend.app.ml_engine import predict_congestion
except ModuleNotFoundError:
    from app.network_data import NODES, TIME_WINDOWS, AVG_VEHICLE_SPACING_M, NodeConfig
    from app.ml_engine import predict_congestion



STEP_MINUTES = 5  # simulation resolution


@dataclass
class StepRecord:
    minute: int
    arrivals_veh_hr: float
    capacity_veh_hr: float
    queue_veh: float
    departures_veh_hr: float
    saturation: float          # degree of saturation x = arrival/capacity
    green_s: int
    reroute_fraction: float
    congestion_class: str
    congestion_prob: float


@dataclass
class NodeResult:
    node_id: str
    name: str
    steps: List[StepRecord] = field(default_factory=list)

    def summary(self) -> Dict:
        n = len(self.steps)
        avg_queue_veh = sum(s.queue_veh for s in self.steps) / n
        max_queue_veh = max(s.queue_veh for s in self.steps)
        avg_throughput = sum(s.departures_veh_hr for s in self.steps) / n
        avg_saturation = sum(s.saturation for s in self.steps) / n

        # Little's Law per step, time-weighted, avoids div-by-zero at t=0
        delays = []
        for s in self.steps:
            veh_per_step = s.departures_veh_hr * (STEP_MINUTES / 60.0)
            if veh_per_step > 0.5:
                delay_s = (s.queue_veh / max(s.departures_veh_hr, 1)) * 3600.0
                delays.append(min(delay_s, 240.0))  # clamp runaway values
        avg_delay_s = sum(delays) / len(delays) if delays else 0.0

        # majority-vote congestion class across the window, weighted to the peak
        classes = [s.congestion_class for s in self.steps]
        cls = max(set(classes), key=classes.count)
        probs = [s.congestion_prob for s in self.steps if s.congestion_class == cls]
        avg_prob = sum(probs) / len(probs) if probs else 0.0

        avg_speed_kmh = _saturation_to_speed_kmh(avg_saturation)

        return {
            "nodeId": self.node_id,
            "name": self.name,
            "avgDelaySec": round(avg_delay_s, 1),
            "avgQueueVeh": round(avg_queue_veh, 1),
            "maxQueueMeters": round(max_queue_veh * AVG_VEHICLE_SPACING_M, 0),
            "avgThroughputVehHr": round(avg_throughput, 0),
            "avgSpeedKmh": round(avg_speed_kmh, 1),
            "degreeOfSaturation": round(avg_saturation, 2),
            "congestionClass": cls,
            "congestionProb": round(avg_prob * 100, 1),
        }


def _saturation_to_speed_kmh(x: float, free_flow_kmh: float = 45.0, jam_kmh: float = 6.0) -> float:
    """Greenshields-style linear speed/saturation relation, clamped to [jam, free_flow]."""
    x = max(0.0, min(x, 1.3))
    speed = free_flow_kmh * (1 - min(x, 1.0)) + jam_kmh * min(x, 1.0)
    return max(jam_kmh, min(speed, free_flow_kmh))


def _demand_profile(fraction_through_window: float) -> float:
    """Single-hump intensity curve in [0.6, 1.0] peaking mid-window."""
    return 0.6 + 0.4 * math.sin(math.pi * fraction_through_window)


def run_simulation(
    time_window: str,
    scenario: str,
    demand_multiplier: float = 1.0,
    lane_closure: bool = False,
    corridor: str = "corridor-a",
) -> Dict[str, NodeResult]:
    """Run one scenario ('baseline' or 'proposed') over one time window.

    Returns {node_id: NodeResult} for every node in the given corridor.
    """
    if time_window not in TIME_WINDOWS:
        raise ValueError(f"unknown time_window '{time_window}'")
    if scenario not in ("baseline", "proposed"):
        raise ValueError(f"unknown scenario '{scenario}'")

    duration_minutes = TIME_WINDOWS[time_window]["duration_minutes"]
    capacity_factor = 0.85 if lane_closure else 1.0  # lane closure ~ -15% capacity

    nodes = {nid: cfg for nid, cfg in NODES.items() if cfg.corridor == corridor}
    queues: Dict[str, float] = {nid: 0.0 for nid in nodes}
    results: Dict[str, NodeResult] = {
        nid: NodeResult(node_id=nid, name=cfg.name) for nid, cfg in nodes.items()
    }
    # "detector state" from the previous step - control decisions react to
    # this, not to the current step's demand, modeling the real detection/
    # actuation lag of an adaptive signal controller (and avoiding
    # unrealistic perfect-foresight control that would erase all queueing).
    prev_state: Dict[str, tuple] = {nid: ("LOW", 0.0, 0.0) for nid in nodes}

    n_steps = duration_minutes // STEP_MINUTES
    for step in range(n_steps):
        minute = step * STEP_MINUTES
        frac = minute / duration_minutes
        intensity = _demand_profile(frac)

        raw_arrivals: Dict[str, float] = {}
        for nid, cfg in nodes.items():
            peak = cfg.peak_volume_veh_hr[time_window]
            raw_arrivals[nid] = peak * intensity * demand_multiplier

        green_s: Dict[str, int] = {nid: cfg.base_green_s for nid, cfg in nodes.items()}
        reroute_out: Dict[str, float] = {nid: 0.0 for nid in nodes}

        if scenario == "proposed":
            for nid, cfg in nodes.items():
                cls, prob, saturation = prev_state[nid]
                if cls == "HIGH":
                    green_s[nid] = min(cfg.max_green_s, cfg.base_green_s + 18)
                    candidates = [
                        nb for nb in cfg.neighbors
                        if nb in nodes and prev_state.get(nb, ("LOW", 0, 1.0))[2] < 0.75
                    ]
                    if candidates:
                        target = min(candidates, key=lambda nb: prev_state[nb][2])
                        reroute_frac = 0.20
                        diverted = raw_arrivals[nid] * reroute_frac
                        reroute_out[nid] = reroute_frac
                        raw_arrivals[nid] -= diverted
                        raw_arrivals[target] = raw_arrivals.get(target, 0) + diverted
                elif cls == "MODERATE":
                    green_s[nid] = min(cfg.max_green_s, cfg.base_green_s + 8)

        # --- advance the queueing model one step per node, then classify the
        #     resulting state - this becomes next step's control input ---
        new_state: Dict[str, tuple] = {}
        for nid, cfg in nodes.items():
            capacity_hr = cfg.lanes * cfg.saturation_flow_per_lane * (green_s[nid] / cfg.cycle_length_s) * capacity_factor
            arrivals_veh = raw_arrivals[nid] * (STEP_MINUTES / 60.0)
            capacity_veh = capacity_hr * (STEP_MINUTES / 60.0)

            departures_veh = min(queues[nid] + arrivals_veh, capacity_veh)
            queues[nid] = max(0.0, queues[nid] + arrivals_veh - departures_veh)

            saturation = raw_arrivals[nid] / capacity_hr if capacity_hr > 0 else 0
            speed_kmh = _saturation_to_speed_kmh(saturation)
            cls, prob = predict_congestion(
                volume_veh_hr=raw_arrivals[nid],
                speed_kmh=speed_kmh,
                queue_veh=queues[nid],
                time_period=time_window,
            )
            new_state[nid] = (cls, prob, saturation)

            results[nid].steps.append(StepRecord(
                minute=minute,
                arrivals_veh_hr=round(raw_arrivals[nid], 1),
                capacity_veh_hr=round(capacity_hr, 1),
                queue_veh=queues[nid],
                departures_veh_hr=round(departures_veh * (60 / STEP_MINUTES), 1),
                saturation=saturation,
                green_s=green_s[nid],
                reroute_fraction=reroute_out[nid],
                congestion_class=cls,
                congestion_prob=prob,
            ))

        prev_state = new_state

    return results


def corridor_summary(node_results: Dict[str, NodeResult], time_window: str) -> Dict:
    """Aggregate per-node summaries into one corridor-level scorecard,
    matching the shape the frontend's DEMO_SCENARIOS objects used."""
    summaries = [r.summary() for r in node_results.values()]
    n = len(summaries)

    avg_delay = sum(s["avgDelaySec"] for s in summaries) / n
    avg_queue_m = sum(s["maxQueueMeters"] for s in summaries) / n
    total_throughput = sum(s["avgThroughputVehHr"] for s in summaries)
    avg_saturation = sum(s["degreeOfSaturation"] for s in summaries) / n

    classes = [s["congestionClass"] for s in summaries]
    overall_class = max(set(classes), key=classes.count)
    probs = [s["congestionProb"] for s in summaries if s["congestionClass"] == overall_class]
    overall_prob = sum(probs) / len(probs) if probs else 0.0

    free_flow_total_s = sum(cfg.free_flow_travel_time_s for cfg in NODES.values())
    travel_time_min = round((free_flow_total_s + avg_delay * n) / 60.0, 1)

    pill = "green" if overall_class == "LOW" else ("amber" if overall_class == "MODERATE" else "red")

    return {
        "avgDelay": round(avg_delay),
        "queueLength": round(avg_queue_m),
        "travelTime": travel_time_min,
        "throughput": round(total_throughput),
        "congestionClass": overall_class,
        "congestionProb": f"{overall_prob:.1f}%",
        "congestionIndex": f"{avg_saturation:.2f}",
        "pillClass": pill,
        "timeWindow": time_window,
    }
