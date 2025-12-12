"""
TraceOS Spark Schemas

Pydantic models for Spark organ state and metadata.

Pivot Phase: Extended with canonical_role and system_alias
for dual-naming architecture (Rosetta Layer).
"""

from typing import Literal, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


OrganType = Literal["cognitive", "affective", "visual", "somatic", "identity", "consolidation"]


class SparkMetadata(BaseModel):
    """
    Metadata describing a Spark organ.

    Dual-Naming Architecture:
    - name/organ_type: Biological metaphor (developer UI)
    - canonical_role/system_alias: Systems vocabulary (engineering docs)

    Both are first-class. Metaphors encode real architectural decisions.
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    organ_type: OrganType
    version: str = "1.0.0"
    description: str = ""

    # Rosetta Layer: Canonical systems-architecture names
    canonical_role: Optional[str] = Field(
        default=None,
        description="Systems-architecture role (e.g., CognitiveEngine, ValuationEngine)"
    )
    system_alias: Optional[str] = Field(
        default=None,
        description="Extended formal name (e.g., Logical Analysis Service)"
    )


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
