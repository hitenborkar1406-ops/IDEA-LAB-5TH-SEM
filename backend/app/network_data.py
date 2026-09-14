"""
Static road-network definition for the corridor.

This replaces a SUMO .net.xml file. Each intersection ("node") is described
by the parameters a deterministic queueing model needs: number of approach
lanes, per-lane saturation flow, signal cycle length, the baseline
(fixed-time) green split, free-flow travel time to the next node, and which
neighboring node it can offload traffic to when it is congested and the
neighbor has spare capacity.

Peak arrival volumes are calibrated so that, at default settings
(demand_multiplier=1.0, no lane closure), the model reproduces the same
baseline order of magnitude used across the project (roughly 780-950
veh/hr at each junction during the peak of the window).
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class NodeConfig:
    node_id: str
    name: str
    corridor: str
    lanes: int
    saturation_flow_per_lane: int   # veh/hr/lane at green
    cycle_length_s: int             # signal cycle length (seconds)
    base_green_s: int               # baseline fixed green time for this approach
    min_green_s: int
    max_green_s: int
    peak_volume_veh_hr: Dict[str, int]   # {"morning": x, "evening": y}
    free_flow_travel_time_s: int         # to next node downstream
    neighbors: List[str] = field(default_factory=list)


# NOTE on saturation_flow_per_lane: classical HCM saturation flow (~1800-1900
# veh/hr/lane) assumes homogeneous passenger-car traffic. Mixed Indian urban
# traffic (two-wheelers, autos, buses sharing a lane, pedestrian conflicts)
# has substantially lower effective capacity per lane. Values below are
# calibrated so peak-hour baseline demand pushes degree-of-saturation into
# the 0.85-0.95 (HIGH) range at these four historically congested junctions.
NODES: Dict[str, NodeConfig] = {
    # Corridor A: Sitabuldi Junction & Variety Sq Network
    "node-1": NodeConfig(
        node_id="node-1", name="Intersection 1: Variety Square Junction", corridor="corridor-a",
        lanes=3, saturation_flow_per_lane=550, cycle_length_s=90, base_green_s=45, min_green_s=30, max_green_s=63,
        peak_volume_veh_hr={"morning": 950, "evening": 1010}, free_flow_travel_time_s=110, neighbors=["node-3"],
    ),
    "node-2": NodeConfig(
        node_id="node-2", name="Intersection 2: Samvidhan Square (RBI Sq.)", corridor="corridor-a",
        lanes=3, saturation_flow_per_lane=510, cycle_length_s=90, base_green_s=42, min_green_s=28, max_green_s=60,
        peak_volume_veh_hr={"morning": 820, "evening": 880}, free_flow_travel_time_s=95, neighbors=["node-3"],
    ),
    "node-3": NodeConfig(
        node_id="node-3", name="Intersection 3: Zero Mile Landmark Sq.", corridor="corridor-a",
        lanes=2, saturation_flow_per_lane=810, cycle_length_s=90, base_green_s=44, min_green_s=28, max_green_s=61,
        peak_volume_veh_hr={"morning": 910, "evening": 970}, free_flow_travel_time_s=100, neighbors=["node-2", "node-4"],
    ),
    "node-4": NodeConfig(
        node_id="node-4", name="Intersection 4: Rani Jhansi Square Corridor", corridor="corridor-a",
        lanes=2, saturation_flow_per_lane=765, cycle_length_s=90, base_green_s=40, min_green_s=26, max_green_s=58,
        peak_volume_veh_hr={"morning": 780, "evening": 840}, free_flow_travel_time_s=90, neighbors=["node-3"],
    ),

    # Corridor B: Wardha Road Highway (Airport Sq to Rahate Colony)
    "node-b1": NodeConfig(
        node_id="node-b1", name="Intersection B1: Airport Square Junction", corridor="corridor-b",
        lanes=4, saturation_flow_per_lane=600, cycle_length_s=100, base_green_s=50, min_green_s=30, max_green_s=70,
        peak_volume_veh_hr={"morning": 1150, "evening": 1250}, free_flow_travel_time_s=120, neighbors=["node-b2"],
    ),
    "node-b2": NodeConfig(
        node_id="node-b2", name="Intersection B2: Chhatrapati Square Junction", corridor="corridor-b",
        lanes=3, saturation_flow_per_lane=560, cycle_length_s=100, base_green_s=48, min_green_s=28, max_green_s=68,
        peak_volume_veh_hr={"morning": 1080, "evening": 1180}, free_flow_travel_time_s=105, neighbors=["node-b1", "node-b3"],
    ),
    "node-b3": NodeConfig(
        node_id="node-b3", name="Intersection B3: Kriplani Square Junction", corridor="corridor-b",
        lanes=3, saturation_flow_per_lane=540, cycle_length_s=100, base_green_s=45, min_green_s=26, max_green_s=65,
        peak_volume_veh_hr={"morning": 980, "evening": 1050}, free_flow_travel_time_s=95, neighbors=["node-b2", "node-b4"],
    ),
    "node-b4": NodeConfig(
        node_id="node-b4", name="Intersection B4: Rahate Colony Square", corridor="corridor-b",
        lanes=3, saturation_flow_per_lane=520, cycle_length_s=100, base_green_s=44, min_green_s=25, max_green_s=62,
        peak_volume_veh_hr={"morning": 940, "evening": 1020}, free_flow_travel_time_s=90, neighbors=["node-b3"],
    ),

    # Corridor C: Central Avenue Commercial Corridor
    "node-c1": NodeConfig(
        node_id="node-c1", name="Intersection C1: Dosar Bhavan Square", corridor="corridor-c",
        lanes=3, saturation_flow_per_lane=500, cycle_length_s=90, base_green_s=42, min_green_s=25, max_green_s=60,
        peak_volume_veh_hr={"morning": 1020, "evening": 1100}, free_flow_travel_time_s=100, neighbors=["node-c2"],
    ),
    "node-c2": NodeConfig(
        node_id="node-c2", name="Intersection C2: Gandhibagh Market Square", corridor="corridor-c",
        lanes=2, saturation_flow_per_lane=700, cycle_length_s=90, base_green_s=40, min_green_s=25, max_green_s=58,
        peak_volume_veh_hr={"morning": 960, "evening": 1040}, free_flow_travel_time_s=90, neighbors=["node-c1", "node-c3"],
    ),
    "node-c3": NodeConfig(
        node_id="node-c3", name="Intersection C3: Telephone Exchange Square", corridor="corridor-c",
        lanes=3, saturation_flow_per_lane=530, cycle_length_s=90, base_green_s=43, min_green_s=26, max_green_s=61,
        peak_volume_veh_hr={"morning": 890, "evening": 950}, free_flow_travel_time_s=95, neighbors=["node-c2"],
    ),

    # Corridor D: Amravati Road Axis
    "node-d1": NodeConfig(
        node_id="node-d1", name="Intersection D1: Law College Square", corridor="corridor-d",
        lanes=3, saturation_flow_per_lane=580, cycle_length_s=95, base_green_s=46, min_green_s=28, max_green_s=64,
        peak_volume_veh_hr={"morning": 990, "evening": 1060}, free_flow_travel_time_s=105, neighbors=["node-d2"],
    ),
    "node-d2": NodeConfig(
        node_id="node-d2", name="Intersection D2: University Campus Square", corridor="corridor-d",
        lanes=3, saturation_flow_per_lane=550, cycle_length_s=95, base_green_s=44, min_green_s=26, max_green_s=62,
        peak_volume_veh_hr={"morning": 920, "evening": 980}, free_flow_travel_time_s=95, neighbors=["node-d1"],
    ),
}


TIME_WINDOWS = {
    "morning": {"label": "09:00 - 12:00", "start_minute": 0, "duration_minutes": 180},
    "evening": {"label": "16:00 - 19:00", "start_minute": 0, "duration_minutes": 180},
}

AVG_VEHICLE_SPACING_M = 7.5  # queued vehicle spacing, used to convert veh -> meters
