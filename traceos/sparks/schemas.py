"""
TraceOS Spark Schemas

Pydantic models for Spark organ state and metadata.
"""

from typing import Literal, Any
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


OrganType = Literal["cognitive", "affective", "visual", "somatic", "identity", "consolidation"]


class SparkMetadata(BaseModel):
    """Metadata describing a Spark organ."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    organ_type: OrganType
    version: str = "1.0.0"
    description: str = ""


class SparkState(BaseModel):
    """
    Current state of a Spark organ.

    Each Spark maintains persistent state that evolves
    through interactions and learning.
    """

    spark_id: UUID
    active: bool = True
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    state_data: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class SparkResponse(BaseModel):
    """Response from a Spark evaluation."""

    spark_id: UUID
    status: Literal["approve", "reject", "abstain"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
