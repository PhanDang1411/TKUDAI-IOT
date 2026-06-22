from __future__ import annotations

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class TelemetryPoint(BaseModel):
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp if available")
    value: float = Field(..., description="Main sensor value")
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[float] = None


class AnomalyRequest(BaseModel):
    target: str = "temperature"
    current_value: float
    recent_values: List[float] = Field(default_factory=list)
    threshold_z: float = 2.5


class ForecastRequest(BaseModel):
    target: str = "co2"
    recent_values: List[float]
    horizon_minutes: int = 15
    model_version: str = "moving_average_baseline_v1"


class RiskRequest(BaseModel):
    target: str = "co2"
    predicted_value: float
    warning_threshold: float = 1000.0
    high_threshold: float = 1200.0


class PredictionItem(BaseModel):
    rank: int
    class_id: int
    class_name: str
    confidence: float
