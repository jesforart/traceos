"""
Creative DNA Schemas for TraceOS

Defines core models for StyleSignatures and DNA lineage.
This is how TraceOS remembers its creative identity over time.

@provenance traceos_dna_v1
@organ identity
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class StyleMetric(BaseModel):
    """
    Single named metric contributing to style DNA.

    Examples:
    - file_structure_complexity
    - doc_coverage
    - identity_alignment
    - gut_vibe_score
    """
    name: str
    value: float
    weight: float = 1.0
    description: str = ""


class StyleSignature(BaseModel):
    """
    Creative DNA snapshot for a given derivation/evaluation.

    This is how TraceOS remembers 'who' a piece of work feels like.
    Each signature captures the style DNA of a single derivation.
    """
    signature_id: str = Field(..., description="Unique signature ID")
    intent_id: str = Field(..., description="Associated intent ID")
    derive_id: str = Field(..., description="Associated derivation ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    metrics: Dict[str, StyleMetric] = Field(
        default_factory=dict,
        description="Named metrics contributing to DNA"
    )

    embedding: List[float] = Field(
        default_factory=list,
        description="Dense numeric vector representation of style"
    )

    notes: str = Field(
        default="",
        description="Human-readable description of the style snapshot"
    )


class DNALineageNode(BaseModel):
    """
    Node in DNA lineage graph.

    Represents how signatures evolve over time.
    Tracks parent-child relationships and alignment scores.
    """
    signature_id: str
    parent_signature_id: Optional[str] = None
    intent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    alignment_to_parent: Optional[float] = None  # 0-1, cosine similarity


class DNAProfileSummary(BaseModel):
    """
    Aggregated DNA profile for reporting & UI.

    Summarizes the organism's creative evolution over time.
    """
    latest_signature_id: Optional[str] = None
    total_signatures: int = 0
    average_alignment: Optional[float] = None
    notes: str = ""
    last_updated: datetime = Field(default_factory=datetime.utcnow)
