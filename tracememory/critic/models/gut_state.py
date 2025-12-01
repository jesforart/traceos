"""
Gut State Models

The Gut tastes interaction events and derives emotional state.
These Pydantic models define the schema for valuation data.

@provenance intent_gut_taste_001
@organ valuation
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class MoodState(str, Enum):
    """
    The five emotional states the Gut can sense.
    Named as feelings, not technical states.
    """
    CALM = "Calm"
    FLOW = "Flow"
    FRUSTRATION = "Frustration"
    CHAOS = "Chaos"
    EXPLORATION = "Exploration"


class ResonanceEvent(BaseModel):
    """
    A single taste of user interaction.

    The Gut senses these micro-reactions and accumulates
    them into frustration_index and flow_probability.
    """
    type: str = Field(
        ...,
        description="Event type: stroke_accept, stroke_reject, undo, redo, ghost_accept, ghost_reject, pause_detected"
    )
    timestamp: float = Field(
        ...,
        description="When this happened (client performance.now() or server time)"
    )
    session_id: str = Field(
        ...,
        description="Which session this belongs to"
    )
    latency_ms: Optional[float] = Field(
        None,
        description="Time between action and user response in milliseconds"
    )
    erratic_input: Optional[bool] = Field(
        None,
        description="Flag for erratic input detection (Chaos trigger)"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for this event"
    )

    class Config:
        # Allow population by field name or alias
        populate_by_name = True


class GutState(BaseModel):
    """
    The Gut's current emotional state.

    This is the output of the valuation organ — a synthesis
    of all recent micro-reactions into actionable feeling.

    CONSTRAINT: Only the Valuation organ may mutate GutState.
    Brain, Vision, and other organs receive read-only views.
    """
    mood: MoodState = Field(
        ...,
        description="Current dominant mood"
    )
    frustration_index: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How frustrated is the user? (0-1). >0.7 reduces AI creativity"
    )
    flow_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How likely is the user in flow? (0-1). >0.8 increases exploration"
    )
    last_updated: datetime = Field(
        ...,
        description="When this state was last calculated"
    )

    class Config:
        # Use enum values in JSON serialization
        use_enum_values = True


class TasteProfile(BaseModel):
    """
    Accumulated taste preferences that affect future sensing.

    Over time, the Gut develops preferences — certain patterns
    of interaction that consistently lead to flow or frustration.
    """
    baseline_undo_latency_ms: float = Field(
        default=300.0,
        description="User's typical undo latency (baseline)"
    )
    baseline_accept_latency_ms: float = Field(
        default=150.0,
        description="User's typical acceptance latency (baseline)"
    )
    flow_associated_techniques: list[str] = Field(
        default_factory=list,
        description="Techniques that correlate with flow states"
    )
    frustration_triggers: list[str] = Field(
        default_factory=list,
        description="Patterns that correlate with frustration"
    )
    calibrated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last calibration timestamp"
    )
