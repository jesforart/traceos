"""
Spark Organ Schemas

Defines the data models for TraceOS cognitive organs.

@provenance traceos_sparks_v1
@organ kernel
"""

from datetime import datetime
from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field


class SparkMetadata(BaseModel):
    """Metadata describing a Spark organ."""
    name: str
    organ_type: Literal["cognitive", "affective", "visual", "identity"]
    description: str
    version: str = "1.0"


class SparkState(BaseModel):
    """
    Persistent state of a Spark organ.

    State evolves over time based on evaluations and events.
    """
    activation: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Current activity level (0=dormant, 1=hyperactive)"
    )
    fatigue: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Metabolic cost accumulation (0=fresh, 1=exhausted)"
    )
    mood: str = Field(
        "neutral",
        description="Current emotional state (neutral, excited, frustrated, flowing)"
    )
    memory: Dict[str, Any] = Field(
        default_factory=dict,
        description="Organ-specific memory storage"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)
