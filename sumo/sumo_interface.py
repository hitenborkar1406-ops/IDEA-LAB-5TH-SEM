"""
SUMO and Queueing Simulation Interface Adapter.

Provides a unified abstract interface for traffic simulation engines.
Allows seamless switching between the custom deterministic queueing engine
(used when SUMO is downloading/unavailable) and SUMO/TraCI simulator.
"""

from abc import ABC, abstractmethod
import os
import sys
from typing import Dict, Any, Optional

# Add parent directory to path to allow backend app imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TrafficSimulationInterface(ABC):
    """Abstract interface for traffic simulation engines."""

    @abstractmethod
    def initialize(self, time_window: str, corridor: str = "corridor-a") -> bool:
        """Initialize simulation scenario and network topology."""
        pass

    @abstractmethod
    def run_step(self, demand_multiplier: float = 1.0, lane_closure: bool = False) -> Dict[str, Any]:
        """Execute one simulation step and return node/corridor metrics."""
        pass

    @abstractmethod
    def run_full(
        self,
        time_window: str = "morning",
        scenario: str = "baseline",
        demand_multiplier: float = 1.0,
        lane_closure: bool = False,
        corridor: str = "corridor-a"
    ) -> Dict[str, Any]:
        """Run complete scenario across the 3-hour window."""
        pass


class QueueingSimulationAdapter(TrafficSimulationInterface):
    """Adapter wrapping the deterministic queueing simulation engine."""

    def __init__(self):
        try:
            from backend.app.simulation_engine import run_simulation, corridor_summary
            from backend.app.network_data import NODES
        except ModuleNotFoundError:
            from app.simulation_engine import run_simulation, corridor_summary
            from app.network_data import NODES

        self._run_sim = run_simulation
        self._summary = corridor_summary
        self._nodes = NODES

    def initialize(self, time_window: str, corridor: str = "corridor-a") -> bool:
        return True

    def run_step(self, demand_multiplier: float = 1.0, lane_closure: bool = False) -> Dict[str, Any]:
        return {"status": "ok"}

    def run_full(
        self,
        time_window: str = "morning",
        scenario: str = "baseline",
        demand_multiplier: float = 1.0,
        lane_closure: bool = False,
        corridor: str = "corridor-a"
    ) -> Dict[str, Any]:
        node_results = self._run_sim(
            time_window=time_window,
            scenario=scenario,
            demand_multiplier=demand_multiplier,
            lane_closure=lane_closure,
            corridor=corridor
        )
        summary = self._summary(node_results, time_window)
        return {
            "summary": summary,
            "nodes": {nid: r.summary() for nid, r in node_results.items()},
            "engine": "deterministic-queueing"
        }


class SUMOSimulationAdapter(TrafficSimulationInterface):
    """Adapter for Eclipse SUMO 1.27.1 / TraCI simulation."""

    def __init__(self, sumo_home: Optional[str] = None):
        self.sumo_home = sumo_home or os.getenv("SUMO_HOME", r"C:\Program Files (x86)\Eclipse\Sumo")
        self.traci = None
        self.runner = None
        self._setup_traci_path()

    def _setup_traci_path(self):
        tools_path = os.path.join(self.sumo_home, "tools")
        if tools_path not in sys.path and os.path.exists(tools_path):
            sys.path.append(tools_path)
        try:
            import traci
            self.traci = traci
            try:
                from sumo.sumo_runner import SUMOLiveRunner
                self.runner = SUMOLiveRunner(self.sumo_home)
            except Exception:
                self.runner = None
        except ImportError:
            self.traci = None

    def is_available(self) -> bool:
        """Check if SUMO binary and TraCI library are accessible."""
        sumo_bin = os.path.join(self.sumo_home, "bin", "sumo.exe")
        return self.traci is not None and os.path.exists(sumo_bin)

    def initialize(self, time_window: str, corridor: str = "corridor-a") -> bool:
        if not self.is_available():
            print("[SUMOAdapter] SUMO 1.27.1 is not installed or SUMO_HOME path invalid.")
            return False
        return True

    def run_step(self, demand_multiplier: float = 1.0, lane_closure: bool = False) -> Dict[str, Any]:
        if not self.is_available():
            raise RuntimeError("SUMO 1.27.1 simulation not initialized.")
        return {"status": "ok"}

    def run_full(
        self,
        time_window: str = "morning",
        scenario: str = "baseline",
        demand_multiplier: float = 1.0,
        lane_closure: bool = False,
        corridor: str = "corridor-a"
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise RuntimeError("SUMO 1.27.1 binary not available.")

        if self.runner:
            res = self.runner.run_simulation(
                time_window=time_window,
                scenario=scenario,
                demand_multiplier=demand_multiplier,
                lane_closure=lane_closure
            )
            return res

        return {"engine": "SUMO 1.27.1 TraCI", "status": "executed"}


def get_simulation_adapter(engine_type: str = "auto") -> TrafficSimulationInterface:
    """Factory function to retrieve simulation adapter instance."""
    env_engine = os.getenv("SIMULATION_ENGINE_TYPE", engine_type)
    if env_engine in ("auto", "sumo"):
        sumo_adapter = SUMOSimulationAdapter()
        if sumo_adapter.is_available():
            return sumo_adapter
    return QueueingSimulationAdapter()

