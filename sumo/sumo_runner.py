"""
SUMO 1.27.1 Microscopic Simulation & TraCI Controller.

Manages Eclipse SUMO process lifecycle, TraCI socket connection,
real-time vehicle telemetry, and live rerouting detection via TraCI.

This module wraps sitabuldi_sim.py's real TraCI simulation and exposes
a consistent interface for the backend API.
"""

import os
import sys
import json
import math
from typing import Dict, Any, Optional

DEFAULT_SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def setup_sumo_env() -> str:
    sumo_home = os.getenv("SUMO_HOME", DEFAULT_SUMO_HOME)
    tools = os.path.join(sumo_home, "tools")
    if tools not in sys.path and os.path.exists(tools):
        sys.path.append(tools)
    return sumo_home

def is_sumo_available() -> bool:
    sumo_home = setup_sumo_env()
    sumo_bin = os.path.join(sumo_home, "bin", "sumo.exe")
    if not os.path.exists(sumo_bin):
        return False
    try:
        import traci
        return True
    except ImportError:
        return False


class SUMOLiveRunner:
    """
    Live TraCI simulation execution runner for SUMO 1.27.1.

    Delegates to sitabuldi_sim.py for the actual TraCI simulation loop.
    The run_simulation() method triggers a real SUMO process via TraCI,
    steps it forward in time, collects vehicle telemetry, detects reroute
    events, and writes sim_output.json — no formula-based estimates.
    """

    def __init__(self, sumo_home: Optional[str] = None):
        self.sumo_home = sumo_home or setup_sumo_env()
        self.traci = None
        self.active_label = "smart_traffic_sim"
        self.is_connected = False

    def connect(self) -> bool:
        if not is_sumo_available():
            print(f"[SUMOLiveRunner] SUMO 1.27.1 not found at {self.sumo_home}")
            return False
        import traci
        self.traci = traci
        self.is_connected = True
        return True

    def run_simulation(
        self,
        net_file: Optional[str] = None,
        demand_file: Optional[str] = None,
        sim_steps: int = 800,
        rerouting_probability: float = 1.0,
        rerouting_period: int = 20,
    ) -> Dict[str, Any]:
        """
        Run a real SUMO/TraCI microscopic simulation.

        Calls traci.start() with the provided network and demand files,
        steps the simulation via traci.simulationStep(), records per-step
        vehicle telemetry (position, speed, edge), detects reroute events
        (SUMO rerouting device reassignments + edge-sequence deviations),
        writes sim_output.json, and returns a summary dict.

        Parameters
        ----------
        net_file   : path to .net.xml (defaults to sitabuldi_junction.net.xml)
        demand_file: path to .rou.xml  (defaults to sitabuldi_demand.rou.xml)
        sim_steps  : number of simulation steps (1 step = 1 second)
        rerouting_probability : fraction of vehicles equipped with rerouting device
        rerouting_period      : how often (seconds) rerouting device re-evaluates route

        Returns
        -------
        dict with keys: steps_run, total_vehicles, reroute_event_count,
                        frame_count, output_file, engine
        """
        from sitabuldi_sim import run_simulation as _run_sim, SIM_STEPS, REROUTING_PROBABILITY, REROUTING_PERIOD

        # Allow caller to override module-level constants via monkey-patching
        import sitabuldi_sim as _sim_mod
        _sim_mod.SIM_STEPS             = sim_steps
        _sim_mod.REROUTING_PROBABILITY = rerouting_probability
        _sim_mod.REROUTING_PERIOD      = rerouting_period
        if net_file:
            _sim_mod.NET_FILE = net_file
        if demand_file:
            _sim_mod.DEMAND_FILE = demand_file

        output = _run_sim()
        meta = output.get("meta", {})

        return {
            "engine":              "SUMO 1.27.1 TraCI",
            "steps_run":           meta.get("steps_run", 0),
            "total_vehicles":      meta.get("total_vehicles", 0),
            "reroute_event_count": meta.get("reroute_event_count", 0),
            "frame_count":         len(output.get("frames", [])),
            "edge_count":          len(output.get("edges", [])),
            "output_file":         os.path.join(SCRIPT_DIR, "sim_output.json"),
            "junction_id":         meta.get("junction_id"),
            "junction_lon":        meta.get("junction_lon"),
            "junction_lat":        meta.get("junction_lat"),
        }

    def load_last_output(self) -> Dict[str, Any]:
        """Load and return the most recent sim_output.json from disk."""
        output_file = os.path.join(SCRIPT_DIR, "sim_output.json")
        if not os.path.exists(output_file):
            raise FileNotFoundError(
                f"sim_output.json not found. Run run_simulation() first."
            )
        with open(output_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def close(self):
        """Close TraCI connection if open (sitabuldi_sim closes it internally)."""
        if self.traci and self.is_connected:
            try:
                self.traci.close()
            except Exception:
                pass
            self.is_connected = False
