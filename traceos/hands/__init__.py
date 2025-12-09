"""
TraceOS Hands Module - Somatic Expression System

The Hands module enables TraceOS to express itself through
stroke-based motor output. It integrates:

- DNA: Style memory influencing stroke characteristics
- Gut: Emotional state modulating tremor and pressure
- Hands Spark: Physical fatigue and capacity tracking

Components:
- MotionEngine: Low-level trajectory generation
- StrokePlanner: Organism-aware stroke planning
- HandsSpark: Somatic organ tracking motor state

@provenance traceos_hands_v1
@organ somatic
"""

from .schemas import (
    StrokePoint,
    MotionParams,
    StrokePlan,
    HandsStatus
)
from .engine import MotionEngine
from .planner import StrokePlanner

__all__ = [
    # Schemas
    "StrokePoint",
    "MotionParams",
    "StrokePlan",
    "HandsStatus",

    # Core classes
    "MotionEngine",
    "StrokePlanner"
]
