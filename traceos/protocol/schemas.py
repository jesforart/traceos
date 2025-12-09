"""
TraceOS Protocol Schemas (v1.0)

Defines the formal kernel protocol for Intent → Derive → Test → Evaluate → Codify.
All schemas are JSON-serializable for provenance tracking.

Security Note: These endpoints are for LOCAL DEVELOPMENT ONLY.
Do not expose /v1/trace/* publicly without authentication.

@provenance traceos_protocol_v1
@organ kernel
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============================
# INTENT SCHEMA
# ============================

class IntentMetadata(BaseModel):
    """Metadata for intent attribution."""
    spark: str = Field(..., description="Which organ initiated the request")
    requested_by: str = Field(default="Jessie", description="Human initiator")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Intent(BaseModel):
    """
    Intent Schema - What TraceOS should build.

    Example:
        {
            "intent_id": "intent_20251208_143022",
            "title": "Implement quantum-ready architecture",
            "tags": ["quantum", "gut-spark"],
            "goals": ["Create QuantumCoProcessor interface", "..."],
            "metadata": {"spark": "Brain", "requested_by": "Jessie"}
        }
    """
    intent_id: str = Field(..., description="Unique intent identifier")
    title: str = Field(..., description="Human-readable title")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    goals: List[str] = Field(..., description="Specific objectives to achieve")
    metadata: IntentMetadata


# ============================
# DERIVE OUTPUT SCHEMA
# ============================

class FileChange(BaseModel):
    """Record of a file created or modified."""
    path: str = Field(..., description="Relative path from repo root")
    loc: int = Field(..., description="Lines of code")
    status: Literal["created", "modified"] = Field(..., description="Change type")


class ProvenanceNode(BaseModel):
    """Provenance graph node for design lineage."""
    node_id: str = Field(..., description="Unique provenance node ID")
    parent_intent: str = Field(..., description="Intent ID that spawned this")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeriveOutput(BaseModel):
    """
    Output from /trace:derive - files created with provenance.
    """
    intent_id: str
    derive_id: str = Field(..., description="Unique derivation ID")
    status: Literal["derived", "failed"] = "derived"
    files: List[FileChange] = Field(default_factory=list)
    provenance: ProvenanceNode
    notes: str = Field(default="", description="Implementation notes")


# ============================
# TEST SCHEMA
# ============================

class TestResults(BaseModel):
    """Results from running test suite."""
    typescript: Optional[Literal["passed", "failed"]] = None
    unit_tests: Dict[str, Literal["passed", "failed"]] = Field(default_factory=dict)
    frontend: Optional[Literal["passed", "failed"]] = None
    notebooks: Optional[Literal["import-success", "failed"]] = None
    notes: str = Field(default="")


class TestOutput(BaseModel):
    """Output from /trace:test - validation results."""
    intent_id: str
    derive_id: str
    status: Literal["tests-run", "failed"]
    results: TestResults


# ============================
# EVALUATE SCHEMA
# ============================

class SparkComment(BaseModel):
    """Individual comment from a Spark reviewer."""
    severity: Literal["info", "low", "medium", "high"]
    message: str


class SparkReview(BaseModel):
    """
    Review from a single Spark (Brain, Gut, Eyes, Soul, Dream).

    Phase 2+: Real Spark organs with persistent state.
    Phase 4: Added Dream spark for long-term consolidation.
    """
    spark: Literal["Brain", "Gut", "Eyes", "Soul", "Dream"]
    status: Literal["approve", "approve-with-changes", "reject"]
    score: float = Field(..., ge=0.0, le=1.0, description="Review score 0-1")
    comments: List[SparkComment] = Field(default_factory=list)


class EvaluateOutput(BaseModel):
    """Output from /trace:evaluate - multi-Spark review."""
    intent_id: str
    derive_id: str
    reviews: List[SparkReview]
    overall_status: Literal["approved", "needs-changes", "rejected"]


# ============================
# CODIFY SCHEMA
# ============================

class CodifyOutput(BaseModel):
    """
    Output from /trace:codify - learnings captured.

    Updates Double DNA Engine with design patterns and lessons.
    """
    intent_id: str
    derive_id: str
    codified: Dict[str, Any] = Field(
        default_factory=lambda: {
            "patterns": [],
            "lessons": [],
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================
# DEGRADED MODE SCHEMA
# ============================

class DegradedModeOutput(BaseModel):
    """
    Emergency provenance when normal flow breaks.

    TraceOS never loses provenance, even in degraded mode.
    """
    intent_id: str
    status: Literal["degraded-mode"] = "degraded-mode"
    files_touched: List[str] = Field(default_factory=list)
    llm_used: str = Field(..., description="Which LLM was used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: str
