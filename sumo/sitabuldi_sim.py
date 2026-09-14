"""
sitabuldi_sim.py — Real SUMO/TraCI Simulation for Sitabuldi Junction, Nagpur

This replaces all formula-based fake simulation logic with a genuine SUMO
microscopic simulation using TraCI, rerouting devices, and full telemetry capture.

Network  : sitabuldi_junction.net.xml
Routes   : sitabuldi_demand.rou.xml
Junction : cluster_2347019624_312691688_312691691 (79.086048°E, 21.144963°N)

Output: sim_output.json with:
  - "edges"         : network edge geometry
  - "frames"        : per-step per-vehicle telemetry
  - "reroute_events": detected route deviations
"""

import os
import sys
import json
import time
import math
import subprocess
import tempfile
import traceback
from collections import defaultdict

# --- SUMO setup ---
SUMO_HOME = os.getenv("SUMO_HOME", r"C:\Program Files (x86)\Eclipse\Sumo")
SUMO_TOOLS = os.path.join(SUMO_HOME, "tools")
if SUMO_TOOLS not in sys.path:
    sys.path.append(SUMO_TOOLS)

import traci
import sumolib

# --- File paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NET_FILE     = os.path.join(SCRIPT_DIR, "sitabuldi_junction_tls.net.xml")  # TLS-patched version
DEMAND_FILE  = os.path.join(SCRIPT_DIR, "sitabuldi_demand.rou.xml")
OUTPUT_FILE  = os.path.join(SCRIPT_DIR, "sim_output.json")
SUMO_BIN     = os.path.join(SUMO_HOME, "bin", "sumo.exe")

# --- Simulation parameters ---
SIM_STEPS            = 800        # simulation steps (1 step = 1 second)
TRACI_PORT           = 8813
REROUTING_PROBABILITY = 1.0       # all vehicles can reroute
REROUTING_PERIOD     = 20         # re-evaluate route every 20 steps (seconds)
TELEPORT_TIME        = -1         # disable teleporting (keep jam visible)

# --- UTM Zone 44N offset (from osm.net.xml location tag) ---
NET_OFFSET_X = -292445.79
NET_OFFSET_Y = -2333350.41

def utm44n_to_lonlat(easting, northing):
    """Convert UTM Zone 44N (SUMO internal) coordinates to WGS84 lon/lat."""
    K0, E = 0.9996, 0.00669438
    E2, E3 = E*E, E*E*E
    E_P2 = E / (1.0 - E)
    SQRT_E = math.sqrt(1 - E)
    _E = (1 - SQRT_E) / (1 + SQRT_E)
    _E2, _E3, _E4, _E5 = _E*_E, _E**3, _E**4, _E**5
    M1 = 1 - E/4 - 3*E2/64 - 5*E3/256
    P2 = 3*_E/2 - 27*_E3/32 + 269*_E5/512
    P3 = 21*_E2/16 - 55*_E4/32
    P4 = 151*_E3/96 - 417*_E5/128
    P5 = 1097*_E4/512
    R = 6378137
    x = easting - 500000
    y = northing
    m = y / K0
    mu = m / (R * M1)
    p_rad = mu + P2*math.sin(2*mu) + P3*math.sin(4*mu) + P4*math.sin(6*mu) + P5*math.sin(8*mu)
    p_sin, p_cos = math.sin(p_rad), math.cos(p_rad)
    p_tan = p_sin / p_cos
    ep_sin = 1 - E * p_sin**2
    n_val = R / math.sqrt(ep_sin)
    r_val = (1 - E) / ep_sin
    c = E_P2 * p_cos**2
    d = x / (n_val * K0)
    lat = (p_rad - (p_tan/r_val) *
           (d**2/2 - d**4/24*(5 + 3*p_tan**2 + 10*c - 4*c**2 - 9*E_P2)) +
           d**6/720*(61 + 90*p_tan**2 + 298*c + 45*p_tan**4 - 252*E_P2 - 3*c**2))
    lon = (d - d**3/6*(1 + 2*p_tan**2 + c) +
           d**5/120*(5 - 2*c + 28*p_tan**2 - 3*c**2 + 8*E_P2 + 24*p_tan**4)) / p_cos
    lon_deg = math.degrees(lon) + (44 - 1)*6 - 180 + 3  # zone 44
    return lon_deg, math.degrees(lat)

def sumo_xy_to_lonlat(x, y):
    """Convert SUMO net (x, y) to WGS84 (lon, lat)."""
    return utm44n_to_lonlat(x - NET_OFFSET_X, y - NET_OFFSET_Y)

def extract_edge_geometries(net_file):
    """Load network edge geometries as GeoJSON-style feature list."""
    print("  Loading network for edge geometries...")
    net = sumolib.net.readNet(net_file, withInternal=False)
    features = []
    for edge in net.getEdges():
        coords = []
        for lane in edge.getLanes():
            shape = lane.getShape()
            lonlat_coords = [sumo_xy_to_lonlat(x, y) for x, y in shape]
            coords.append([[round(lon, 6), round(lat, 6)] for lon, lat in lonlat_coords])
        features.append({
            "id": edge.getID(),
            "from": edge.getFromNode().getID(),
            "to": edge.getToNode().getID(),
            "length": round(edge.getLength(), 2),
            "speed": round(edge.getSpeed(), 2),
            "lanes": edge.getLaneNumber(),
            "coords": coords[0] if coords else []
        })
    print(f"  Extracted geometry for {len(features)} edges.")
    return features

def run_simulation():
    """Main simulation loop using TraCI."""

    # --- Step 1: Extract edge geometries (done before starting SUMO) ---
    print("[SIM] Extracting edge geometries...")
    edge_geometries = extract_edge_geometries(NET_FILE)

    # --- Step 2: Build SUMO command ---
    sumo_cmd = [
        SUMO_BIN,
        "--net-file",            NET_FILE,
        "--route-files",         DEMAND_FILE,
        "--begin",               "0",
        "--end",                 str(SIM_STEPS),
        "--step-length",         "1",
        # Rerouting configuration
        "--device.rerouting.probability", str(REROUTING_PROBABILITY),
        "--device.rerouting.period",      str(REROUTING_PERIOD),
        "--device.rerouting.adaptation-steps", "10",
        # Queue/congestion visibility — disable teleporting so jams form
        "--time-to-teleport",    str(TELEPORT_TIME),
        "--waiting-time-memory", "300",
        # Suppress noisy logging
        "--no-step-log",
        "--error-log",           os.path.join(SCRIPT_DIR, "sumo_error.log"),
        "--message-log",         os.path.join(SCRIPT_DIR, "sumo_messages.log"),
    ]

    print(f"\n[SIM] Starting SUMO with command:")
    print("  " + " ".join(sumo_cmd[:6]) + " ...")
    print(f"  Route file: {DEMAND_FILE}")
    print(f"  Steps: {SIM_STEPS}")

    # --- Step 3: Open TraCI connection ---
    traci.start(sumo_cmd)
    print(f"[SIM] TraCI connection established.")

    # --- State tracking ---
    frames = []
    reroute_events = []
    traffic_lights_log = []            # NEW: per-step TLS data
    vehicle_routes  = {}   # {veh_id: list_of_edges_at_assignment}
    vehicle_seen_edges = defaultdict(list)  # {veh_id: [edges visited in order]}
    total_steps_run = 0
    total_vehicles  = set()
    step_print_interval = 50

    # --- Discover TLS IDs once after simulation starts ---
    tls_id_list = []   # filled on first step

    print(f"\n[SIM] Running {SIM_STEPS} simulation steps...")
    print(f"  Rerouting: probability={REROUTING_PROBABILITY}, period={REROUTING_PERIOD}s")
    print()

    sim_start_wall = time.time()

    try:
        for step in range(SIM_STEPS):
            traci.simulationStep()
            total_steps_run += 1
            sim_time = traci.simulation.getTime()

            # --- Discover TLS IDs on first step --------------------------------
            if total_steps_run == 1:
                tls_id_list = list(traci.trafficlight.getIDList())
                print(f"  [TLS] Found {len(tls_id_list)} traffic light(s): {tls_id_list}")

            # --- Log traffic light states ---------------------------------------
            for tls_id in tls_id_list:
                try:
                    phase_idx       = traci.trafficlight.getPhase(tls_id)
                    phase_state     = traci.trafficlight.getRedYellowGreenState(tls_id)
                    next_switch_abs = traci.trafficlight.getNextSwitch(tls_id)
                    seconds_until   = round(next_switch_abs - sim_time, 1)
                    traffic_lights_log.append({
                        "id":                 tls_id,
                        "time":               round(sim_time, 1),
                        "current_phase":      phase_idx,
                        "phase_state":        phase_state,
                        "seconds_until_switch": max(0.0, seconds_until)
                    })
                except Exception:
                    pass

            vehicle_ids = traci.vehicle.getIDList()

            for veh_id in vehicle_ids:
                total_vehicles.add(veh_id)

                # Position and state
                x, y    = traci.vehicle.getPosition(veh_id)
                speed   = traci.vehicle.getSpeed(veh_id)
                edge_id = traci.vehicle.getRoadID(veh_id)
                lon, lat = sumo_xy_to_lonlat(x, y)

                frames.append({
                    "time":       round(sim_time, 1),
                    "vehicle_id": veh_id,
                    "x":          round(lon, 6),
                    "y":          round(lat, 6),
                    "edge_id":    edge_id,
                    "speed":      round(speed, 2)
                })

                # --- Reroute detection ---
                # Record initial route at first sighting
                if veh_id not in vehicle_routes:
                    try:
                        route_edges = list(traci.vehicle.getRoute(veh_id))
                        vehicle_routes[veh_id] = route_edges
                    except Exception:
                        vehicle_routes[veh_id] = []

                # Track edges visited (detect deviations from original route)
                if edge_id and not edge_id.startswith(":"):  # skip internal junction edges
                    prev_edges = vehicle_seen_edges[veh_id]
                    orig_route = vehicle_routes.get(veh_id, [])

                    if prev_edges and edge_id not in orig_route:
                        # Vehicle is on an edge NOT in its originally assigned route
                        # -> This is a reroute event
                        old_edge = prev_edges[-1] if prev_edges else "unknown"
                        # Only log once per new edge (avoid duplicate reroute events)
                        if not reroute_events or not (
                            reroute_events[-1]["vehicle_id"] == veh_id and
                            reroute_events[-1]["new_edge"] == edge_id
                        ):
                            reroute_events.append({
                                "vehicle_id": veh_id,
                                "time":       round(sim_time, 1),
                                "old_edge":   old_edge,
                                "new_edge":   edge_id,
                                "orig_route": orig_route,
                                "note":       "vehicle deviated from originally assigned route"
                            })

                    # Also detect mid-trip route *reassignment* via getRoute change
                    try:
                        current_route = list(traci.vehicle.getRoute(veh_id))
                        if current_route != vehicle_routes[veh_id] and vehicle_routes[veh_id]:
                            orig = vehicle_routes[veh_id]
                            if not reroute_events or not (
                                reroute_events[-1]["vehicle_id"] == veh_id and
                                reroute_events[-1].get("type") == "route_reassignment" and
                                reroute_events[-1]["new_edge"] == (current_route[-1] if current_route else "")
                            ):
                                reroute_events.append({
                                    "vehicle_id":  veh_id,
                                    "time":        round(sim_time, 1),
                                    "old_edge":    orig[-1] if orig else "?",
                                    "new_edge":    current_route[-1] if current_route else "?",
                                    "orig_route":  orig,
                                    "new_route":   current_route,
                                    "type":        "route_reassignment",
                                    "note":        "SUMO rerouting device changed vehicle route"
                                })
                            vehicle_routes[veh_id] = current_route
                    except Exception:
                        pass

                    if not prev_edges or prev_edges[-1] != edge_id:
                        vehicle_seen_edges[veh_id].append(edge_id)

            if step % step_print_interval == 0:
                elapsed = time.time() - sim_start_wall
                active = len(vehicle_ids)
                reroutes = len(reroute_events)
                print(f"  Step {step:5d}/{SIM_STEPS} | t={sim_time:.0f}s | active={active:4d} | "
                      f"total_veh={len(total_vehicles):4d} | reroutes={reroutes:4d} | wall={elapsed:.1f}s")

    except traci.exceptions.FatalTraCIError as e:
        print(f"\n[SIM] TraCI simulation ended early: {e}")
    finally:
        try:
            traci.close()
            print("\n[SIM] TraCI connection closed cleanly.")
        except Exception:
            pass

    wall_time = time.time() - sim_start_wall

    # --- Step 4: Summary ---
    print(f"\n{'='*60}")
    print(f"SIMULATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Total steps run      : {total_steps_run}")
    print(f"  Total vehicles       : {len(total_vehicles)}")
    print(f"  Total frame records  : {len(frames)}")
    print(f"  Reroute events       : {len(reroute_events)}")
    print(f"  Wall clock time      : {wall_time:.1f}s")

    if reroute_events:
        print(f"\n  REROUTE SAMPLE (first 5):")
        for ev in reroute_events[:5]:
            print(f"    veh={ev['vehicle_id']} t={ev['time']}s "
                  f"{ev.get('old_edge','?')} -> {ev.get('new_edge','?')} [{ev.get('note','')}]")
    else:
        print(f"\n  Reroute count is 0.")
        print(f"  Suggestions to get reroutes:")
        print(f"    1. Reduce --device.rerouting.period below 20 (try 10)")
        print(f"    2. Increase flow demand (reduce period in demand file below 3.0s)")
        print(f"    3. Enable --device.rerouting.adaptation-weight=0.5 for hysteresis")
        print(f"    4. Run longer (increase SIM_STEPS to 1200)")

    # --- Step 5: Write output JSON ---
    print(f"\n[SIM] Writing output to {OUTPUT_FILE} ...")

    # Build per-TLS indexed summary for frontend (latest phase/countdown per TLS per step)
    tls_summary = {}
    for rec in traffic_lights_log:
        key = (rec["id"], rec["time"])
        tls_summary[key] = rec
    traffic_lights_deduped = list(tls_summary.values())

    output = {
        "meta": {
            "network":    os.path.basename(NET_FILE),
            "demand":     os.path.basename(DEMAND_FILE),
            "steps_run":  total_steps_run,
            "total_vehicles": len(total_vehicles),
            "reroute_event_count": len(reroute_events),
            "rerouting_probability": REROUTING_PROBABILITY,
            "rerouting_period": REROUTING_PERIOD,
            "junction_id": "cluster_2347019624_312691688_312691691",
            "junction_lon": 79.086048,
            "junction_lat": 21.144963,
            "tls_ids": tls_id_list,
        },
        "edges": edge_geometries,
        "frames": frames,
        "reroute_events": reroute_events,
        "traffic_lights": traffic_lights_deduped,   # NEW: TLS state per step
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"[SIM] Output written: {size_mb:.2f} MB ({len(frames)} frame records)")
    return output

if __name__ == "__main__":
    print("=" * 60)
    print("Sitabuldi Junction — Real SUMO/TraCI Simulation")
    print("=" * 60)
    print(f"SUMO: {SUMO_BIN}")
    print(f"Net : {NET_FILE}")
    print(f"Dem : {DEMAND_FILE}")
    print()

    if not os.path.exists(SUMO_BIN):
        print(f"ERROR: SUMO binary not found at {SUMO_BIN}")
        sys.exit(1)
    if not os.path.exists(NET_FILE):
        print(f"ERROR: Network file not found: {NET_FILE}")
        sys.exit(1)
    if not os.path.exists(DEMAND_FILE):
        print(f"ERROR: Demand file not found: {DEMAND_FILE}")
        sys.exit(1)

    result = run_simulation()
    print("\nDone.")
