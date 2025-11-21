from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Tuple, Dict, Any
from datetime import datetime

class PressureDistribution(BaseModel):
    """Statistical distribution of pressure values."""
    min: float
    max: float
    mean: float
    median: float
    std_dev: float
    histogram: List[int] = Field(default_factory=lambda: [0]*10)

class TiltDistribution(BaseModel):
    """Statistical distribution of tilt values."""
    avg_tilt_deg: float
    avg_azimuth_deg: float
    tilt_range: Tuple[float, float]
    mode_tilt_deg: float

class VelocityDistribution(BaseModel):
    """Statistical distribution of velocity values."""
    avg_velocity: float
    max_velocity: float
    p25_velocity: float
    p75_velocity: float

class PhaseDistributions(BaseModel):
    """Distributions for one calibration phase."""
    pressure: PressureDistribution
    tilt: TiltDistribution
    velocity: VelocityDistribution

class BezierCurve(BaseModel):
    """Cubic Bezier curve with 4 control points."""
    control_points: List[Tuple[float, float]]

class ArtistProfile(BaseModel):
    """Complete artist calibration profile."""
    id: str
    artist_name: str
    created_at: int
    version: int = 1

    # Version tracking
    trace_profile_version: str = "1.0.0"
    brush_engine_version: str = "2025.11.12"

    device: Dict[str, Any] = Field(default_factory=dict)
    distributions: Dict[str, Any] = Field(default_factory=dict)
    curves: Dict[str, Any] = Field(default_factory=dict)
    nib: Dict[str, Any] = Field(default_factory=dict)
    stabilizer: Dict[str, Any] = Field(default_factory=dict)

class CalibrationStroke(BaseModel):
    """Stroke captured during calibration."""
    stroke: Dict[str, Any]
    phase: Literal["feather", "normal", "heavy"]
    timestamp: int

class CalibrationSession(BaseModel):
    """Complete calibration session."""
    id: str
    user_id: Optional[str] = None
    strokes: List[CalibrationStroke]
    started_at: int
    completed_at: Optional[int] = None
    current_phase: Literal["feather", "normal", "heavy", "complete"]
    profile: Optional[ArtistProfile] = None

class CompleteCalibrationRequest(BaseModel):
    """Request to complete calibration."""
    session: CalibrationSession
    artist_name: str = "Artist"
