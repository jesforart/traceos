"""
Resonance Event System

Future: Wire frontend events to Spark state updates.

@provenance traceos_sparks_v1
@organ kernel
"""

from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field


class ResonanceEvent(BaseModel):
    """
    Event that can trigger Spark state changes.

    Examples:
    - undo_streak (frustration signal for Gut)
    - save_success (flow signal for Gut)
    - derivation_failure (fatigue signal for Brain)
    """
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Future: Event bus implementation
# For now, Sparks update their own state during evaluation
