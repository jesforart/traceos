"""
TraceOS Protocol Schemas

Pydantic models for the Intent -> Derive -> Evaluate -> Codify workflow.
"""

from typing import Literal
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Intent(BaseModel):
    """
    Design intent specifying what to build.

    Intents capture the creative goals and constraints
    before any implementation work begins.
    """

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=200)
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True


class FileProvenance(BaseModel):
    """Provenance record for a generated file."""

    path: str
    content_hash: str
    source_intent_id: UUID
    generator_version: str


class DeriveOutput(BaseModel):
    """
    Output from the Derive phase.

    Contains generated files with full provenance tracking.
    """

    id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    files: list[FileProvenance] = Field(default_factory=list)
    provenance: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SparkReview(BaseModel):
    """
    Review from a single Spark organ.

    Each Spark evaluates derivations from its specialized perspective.
    """

    spark: Literal["brain", "gut", "eyes", "hands", "soul", "dream"]
    status: Literal["approve", "reject", "abstain"]
    score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvaluationResult(BaseModel):
    """
    Aggregated evaluation from all Spark organs.

    Consensus is reached when sufficient Sparks approve.
    """

    derive_id: UUID
    reviews: list[SparkReview] = Field(default_factory=list)
    consensus: Literal["approved", "rejected", "pending"]
    aggregate_score: float = Field(..., ge=0.0, le=1.0)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class CodifyResult(BaseModel):
    """
    Result of codifying learnings into Creative DNA.

    Captures patterns, preferences, and decisions for future reference.
    """

    evaluation_id: UUID
    patterns_extracted: list[str] = Field(default_factory=list)
    dna_mutations: dict[str, float] = Field(default_factory=dict)
    codified_at: datetime = Field(default_factory=datetime.utcnow)
