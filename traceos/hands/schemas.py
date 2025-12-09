"""
Hands Module Schemas - Stroke Data Models

Defines the data structures for somatic expression:
- StrokePoint: Individual point in trajectory
- MotionParams: Parameters controlling stroke generation
- StrokePlan: Complete stroke with metadata

@provenance traceos_hands_v1
@organ somatic
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StrokePoint(BaseModel):
    """
    A single point in a stroke trajectory.

    Contains position, pressure, velocity, and timing.
    """
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    pressure: float = Field(default=0.5, ge=0.0, le=1.0, description="Stylus pressure 0-1")
    velocity: float = Field(default=1.0, ge=0.0, description="Point-to-point velocity")
    time: float = Field(default=0.0, ge=0.0, description="Time offset from stroke start (ms)")


class MotionParams(BaseModel):
    """
    Parameters controlling stroke trajectory generation.

    These are derived from organism state (Gut mood, Hands fatigue, DNA style).
    """
    # Base parameters
    velocity_base: float = Field(default=1.0, ge=0.1, le=3.0, description="Base velocity multiplier")
    pressure_base: float = Field(default=0.5, ge=0.0, le=1.0, description="Base pressure")
    pressure_gain: float = Field(default=1.0, ge=0.5, le=2.0, description="Pressure multiplier")

    # Smoothing and jitter
    smoothing_factor: float = Field(default=0.5, ge=0.0, le=1.0, description="Trajectory smoothing (0=raw, 1=very smooth)")
    jitter_amount: float = Field(default=0.5, ge=0.0, le=3.0, description="Random tremor/noise amount")

    # Timing
    point_interval_ms: float = Field(default=16.0, ge=1.0, le=100.0, description="Time between points (ms)")


class StrokePlan(BaseModel):
    """
    A complete planned stroke with trajectory and metadata.

    This is the output of the StrokePlanner - ready for execution
    or visualization.
    """
    stroke_id: str = Field(..., description="Unique stroke identifier")
    intent: str = Field(default="generic", description="What this stroke aims to achieve")
    points: List[StrokePoint] = Field(..., description="Ordered trajectory points")
    motion_params: MotionParams = Field(..., description="Parameters used to generate this stroke")
    dna_alignment: float = Field(default=0.0, ge=0.0, le=1.0, description="Alignment to DNA style baseline")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context (gut_mood, fatigue, etc)")

    @property
    def point_count(self) -> int:
        """Number of points in trajectory."""
        return len(self.points)

    @property
    def duration_ms(self) -> float:
        """Total duration in milliseconds."""
        if not self.points:
            return 0.0
        return self.points[-1].time - self.points[0].time


class HandsStatus(BaseModel):
    """
    Current status of the Hands organ.
    """
    fatigue: float = Field(default=0.0, ge=0.0, le=1.0, description="Current fatigue level")
    capacity: float = Field(default=1.0, ge=0.0, le=1.0, description="Current execution capacity")
    stroke_count: int = Field(default=0, ge=0, description="Strokes executed this session")
    activation: float = Field(default=0.0, ge=0.0, le=1.0, description="Current activation level")
