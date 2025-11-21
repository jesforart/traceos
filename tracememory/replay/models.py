"""
Replay system data models

Week 3 - Option D: Next-Gen Replay Engine
Backend data models for provenance and temporal features
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class MomentumStats(BaseModel):
    """Momentum statistics"""
    mean: float
    median: float
    std_dev: float = Field(alias="stdDev")
    min: float
    max: float
    range: float
    entropy: float
    coefficient_of_variation: float = Field(alias="coefficientOfVariation")

    class Config:
        populate_by_name = True


class StrokeClassDistribution(BaseModel):
    """Stroke classification distribution"""
    gesture: int
    detail: int
    shading: int
    corrective: int


class VelocityStats(BaseModel):
    """Velocity statistics"""
    mean_raw: float = Field(alias="meanRaw")
    mean_smoothed: float = Field(alias="meanSmoothed")
    max_raw: float = Field(alias="maxRaw")
    max_smoothed: float = Field(alias="maxSmoothed")
    noise_reduction: float = Field(alias="noiseReduction")

    class Config:
        populate_by_name = True


class PauseStats(BaseModel):
    """Pause statistics"""
    total: int
    micro: int
    thinking: int
    deliberate: int
    mean_duration: float = Field(alias="meanDuration")
    max_duration: float = Field(alias="maxDuration")

    class Config:
        populate_by_name = True


class RhythmMetrics(BaseModel):
    """Drawing rhythm metrics"""
    strokes_per_minute: float = Field(alias="strokesPerMinute")
    average_stroke_duration: float = Field(alias="averageStrokeDuration")
    burstiness: float

    class Config:
        populate_by_name = True


class PressureStats(BaseModel):
    """Pressure statistics"""
    mean: float
    std_dev: float = Field(alias="stdDev")
    min: float
    max: float

    class Config:
        populate_by_name = True


class SpatialStats(BaseModel):
    """Spatial statistics"""
    canvas_utilization: float = Field(alias="canvasUtilization")
    mean_stroke_length: float = Field(alias="meanStrokeLength")
    total_path_length: float = Field(alias="totalPathLength")

    class Config:
        populate_by_name = True


class TemporalFeatures(BaseModel):
    """Complete temporal feature set"""
    session_id: str = Field(alias="sessionId")
    artist_profile_id: Optional[str] = Field(None, alias="artistProfileId")
    session_duration: float = Field(alias="sessionDuration")
    total_strokes: int = Field(alias="totalStrokes")

    stroke_classes: StrokeClassDistribution = Field(alias="strokeClasses")

    momentum: Dict[str, MomentumStats]
    velocity: VelocityStats
    pauses: PauseStats
    rhythm: RhythmMetrics
    pressure: PressureStats
    spatial: SpatialStats

    class Config:
        populate_by_name = True


class ProvenanceMetadata(BaseModel):
    """Provenance record metadata"""
    device_type: str = Field(alias="deviceType")
    canvas_size: Dict[str, int] = Field(alias="canvasSize")
    trace_os_version: str = Field(alias="traceOSVersion")

    class Config:
        populate_by_name = True


class ProvenanceRecord(BaseModel):
    """Provenance record with temporal features"""
    id: str
    artist_profile_id: str = Field(alias="artistProfileId")
    session_id: str = Field(alias="sessionId")
    timestamp: int
    temporal: TemporalFeatures
    authenticity_score: Optional[float] = Field(None, alias="authenticityScore")
    metadata: ProvenanceMetadata

    class Config:
        populate_by_name = True


class AuthenticityComponents(BaseModel):
    """Individual authenticity component scores"""
    temporal_consistency: float = Field(alias="temporalConsistency")
    device_fingerprint: float = Field(alias="deviceFingerprint")
    style_consistency: float = Field(alias="styleConsistency")
    pause_pattern: float = Field(alias="pausePattern")

    class Config:
        populate_by_name = True


class AuthenticityResult(BaseModel):
    """Authenticity verification result"""
    score: float
    confidence: float
    components: AuthenticityComponents
    flags: List[str]


class TemporalProfileUpdate(BaseModel):
    """Update request for artist profile temporal features"""
    momentum_mean: float = Field(alias="momentumMean")
    velocity_mean: float = Field(alias="velocityMean")
    stroke_class_distribution: StrokeClassDistribution = Field(alias="strokeClassDistribution")
    strokes_per_minute: float = Field(alias="strokesPerMinute")
    burstiness: float
    session_count: int = Field(alias="sessionCount")

    class Config:
        populate_by_name = True
