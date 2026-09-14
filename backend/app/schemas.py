from typing import Literal, Optional

from pydantic import BaseModel, Field


class SimulateRequest(BaseModel):
    time_window: Literal["morning", "evening"] = "morning"
    scenario: Literal["baseline", "proposed"] = "baseline"
    demand_multiplier: float = Field(1.0, ge=1.0, le=1.5)
    lane_closure: bool = False
    corridor: str = "corridor-a"


class CompareRequest(BaseModel):
    time_window: Literal["morning", "evening"] = "morning"
    demand_multiplier: float = Field(1.0, ge=1.0, le=1.5)
    lane_closure: bool = False
    corridor: str = "corridor-a"


class MLPredictRequest(BaseModel):
    volume_veh_hr: float = Field(..., ge=0)
    speed_kmh: float = Field(..., ge=0, le=120)
    queue_veh: float = Field(..., ge=0)
    time_period: Literal["morning", "evening"] = "morning"
    node_name: Optional[str] = "Selected Node"
