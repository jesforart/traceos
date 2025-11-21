from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class Point(BaseModel):
    """Point captured from tablet input."""
    x: float
    y: float
    pressure: float = Field(ge=0.0, le=1.0)
    tilt_x: float = Field(ge=-90, le=90)
    tilt_y: float = Field(ge=-90, le=90)
    timestamp: int

class Stroke(BaseModel):
    """Complete stroke data."""
    id: str
    points: List[Point]
    tool: Literal['pen', 'brush', 'eraser', 'marker']
    color: str
    width: float
    semantic_label: Optional[str] = None
    layer_id: str
    created_at: int

class StrokeMetrics(BaseModel):
    """Calculated stroke metrics."""
    avg_pressure: float
    pressure_variance: float
    avg_speed: float
    length: float
    smoothness: float
    bounding_box: dict

class ProcessedStroke(BaseModel):
    """Stroke with calculated metrics."""
    stroke: Stroke
    metrics: StrokeMetrics
    smoothed_points: List[Point]
