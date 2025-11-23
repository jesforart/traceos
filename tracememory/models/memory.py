"""
Memory block models and data structures for MemAgent.

This module defines the core memory structures:

LEGACY (MemAgent v1):
- MemoryBlock: Complete session memory state
- AssetState: Current asset state (SVG/GLTF/etc)
- DesignDNA: Style characteristics and constraints

COGNITIVE KERNEL v2.5 (NEW - Tri-State Memory):
- CognitiveMemoryBlock: Logic Layer - Semantic knowledge graph node
- StyleDNA: Vibe Layer - Aesthetic vector embeddings
- IntentProfile: Mind Layer - Emotional/narrative intent
- TelemetryChunk: Muscle Layer - Stroke telemetry pointer
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import hashlib
import json
import uuid


class AssetType(str, Enum):
    """Supported asset types"""
    SVG = "svg"
    GLTF = "gltf"
    PNG = "png"
    OBJ = "obj"


class AssetState(BaseModel):
    """
    Current asset state.

    Stores the asset content along with metadata.
    Max size enforced via validation.
    """
    type: AssetType
    data: str = Field(..., description="Asset content (SVG string, base64, etc)")
    uri: Optional[str] = None  # mem://svg/hero_var_12.svg
    created_at: datetime
    thumbnail: Optional[str] = None  # Base64 thumbnail
    size_bytes: int = 0

    @validator('data')
    def validate_size(cls, v, values):
        """Validate asset size doesn't exceed limits"""
        max_size = 10 * 1024 * 1024  # 10MB
        size = len(v.encode('utf-8'))
        if size > max_size:
            raise ValueError(f"Asset too large: {size} bytes (max {max_size})")
        # Store size for later reference
        return v

    @validator('size_bytes', always=True)
    def compute_size(cls, v, values):
        """Compute size_bytes from data"""
        if 'data' in values:
            return len(values['data'].encode('utf-8'))
        return v


class DesignDNA(BaseModel):
    """
    Design DNA / Style characteristics.

    Captures the aesthetic profile and constraints for a design,
    used to measure drift and maintain consistency.
    """
    style_embedding_id: Optional[str] = None
    distance_from_root: float = Field(default=0.0, ge=0.0, le=1.0)
    distance_band: Dict[str, float] = Field(
        default={"min": 0.15, "max": 0.55},
        description="Acceptable distance range"
    )
    aesthetic_profile: Dict[str, Any] = Field(
        default_factory=dict,
        description="Style attributes {organic: 0.8, minimal: 0.6}"
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Design constraints {WCAG: 'AA', max_file_size: '2MB'}"
    )


class MemoryBlock(BaseModel):
    """
    Complete memory state for a session.

    This is the primary data structure stored on disk and passed to Claude.
    Contains compressed narrative, current state, and provenance.

    Storage: ~/.memagent/sessions/{session_id}/memory.json
    Max size: 10MB
    """
    # Identity
    session_id: str
    memory_block_id: str = Field(default_factory=lambda: generate_memory_block_id())
    created_at: datetime
    last_updated: datetime

    # Compressed narrative (from HF/Claude)
    summary: str = Field(
        default="Session initialized, no events yet.",
        description="Compressed narrative of session",
        max_length=2048
    )

    # Structured context
    design_intent: str = ""
    key_decisions: List[str] = Field(default_factory=list)
    user_preferences: List[str] = Field(default_factory=list)

    # Current state
    last_asset: Optional[AssetState] = None
    active_modifiers: Dict[str, float] = Field(default_factory=dict)
    pending_tasks: List[Dict[str, Any]] = Field(default_factory=list)

    # Design DNA
    design_dna: Optional[DesignDNA] = None

    # Provenance
    provenance_chain: List[str] = Field(
        default_factory=list,
        description="Node IDs in order [node_001, node_002, ...]"
    )

    # Metadata
    event_count: int = 0
    compression_version: str = "1.0"
    schema_version: str = "1.0"  # For migrations

    # Checksums for integrity
    checksum: Optional[str] = None

    def compute_checksum(self) -> str:
        """
        Compute SHA256 checksum of critical fields.

        Used to detect corruption or tampering.
        """
        # Convert datetime to ISO string for consistent serialization
        last_updated_str = self.last_updated.isoformat() if isinstance(self.last_updated, datetime) else str(self.last_updated)

        critical = {
            "session_id": self.session_id,
            "summary": self.summary,
            "last_updated": last_updated_str,
            "active_modifiers": self.active_modifiers
        }

        data_str = json.dumps(critical, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def validate_checksum(self) -> bool:
        """
        Validate stored checksum against computed checksum.

        Returns:
            True if checksum matches or no checksum stored
            False if checksum mismatch (corruption detected)
        """
        if not self.checksum:
            return True  # No checksum to validate
        return self.checksum == self.compute_checksum()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def generate_memory_block_id() -> str:
    """
    Generate unique memory block ID using ULID.

    Format: mem_{ulid}
    Example: mem_01HBKZ5Y8Q9X2N4V7M1R3P6W0S
    """
    from utils.ulid import generate_ulid
    return f"mem_{generate_ulid()}"


# ==============================================================================
# COGNITIVE KERNEL v2.5 - TRI-STATE MEMORY MODELS
# ==============================================================================

# Centralized ID generator for Cognitive Kernel
def generate_id(prefix: str = "") -> str:
    """Generate consistent IDs across the Cognitive Kernel system"""
    id_str = str(uuid.uuid4())
    return f"{prefix}_{id_str}" if prefix else id_str


# Vector validation constants
STYLE_VECTOR_DIM = 128  # All style vectors must be exactly 128-dim


def validate_vector_dim(
    vector: Optional[List[float]],
    expected_dim: int = STYLE_VECTOR_DIM
) -> Optional[List[float]]:
    """
    Validate vector dimensions to prevent silent corruption.

    RED TEAM FIX #4: Critical - prevents invalid vectors from corrupting storage.
    """
    if vector is None:
        return None

    if len(vector) != expected_dim:
        raise ValueError(
            f"Vector must be exactly {expected_dim} dimensions, got {len(vector)}"
        )

    return vector


class CognitiveMemoryBlock(BaseModel):
    """
    Logic Layer - Semantic knowledge graph node for Cognitive Kernel v2.5

    This is a NEW model for tri-state memory, separate from legacy MemoryBlock.
    """
    id: str = Field(default_factory=lambda: generate_id("mb"))
    session_id: str
    artifact_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # JSON-LD context (NOTE: stored as 'ld_context', not true @context yet)
    ld_context: Dict[str, Any] = Field(
        default_factory=lambda: {
            "@vocab": "http://traceos.ai/schema#",
            "@type": "MemoryBlock"
        },
        description="JSON-LD context for semantic web (v1 placeholder)"
    )

    # Semantic links
    derived_from: Optional[str] = Field(
        None,
        description="UUID of parent MemoryBlock or session"
    )
    intent_profile_id: Optional[str] = None
    style_dna_id: Optional[str] = None

    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StyleDNA(BaseModel):
    """
    Vibe Layer - Aesthetic vector embeddings (v1: PLACEHOLDER VECTORS)

    RED TEAM FIX #4: All vectors validated to be exactly 128-dim.
    """
    id: str = Field(default_factory=lambda: generate_id("style"))
    artifact_id: str

    # NOTE: These are v1 placeholder embeddings, not production-grade inference
    # Each is 128-dim (validated on assignment)
    stroke_dna: Optional[List[float]] = Field(
        None,
        description="Placeholder: stroke telemetry heuristics (128-dim, validated)"
    )
    image_dna: Optional[List[float]] = Field(
        None,
        description="Placeholder: visual feature heuristics (128-dim, validated)"
    )
    temporal_dna: Optional[List[float]] = Field(
        None,
        description="Placeholder: rhythm/timing heuristics (128-dim, validated)"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Precomputed for fast similarity
    l2_norm: Optional[float] = None
    checksum: Optional[str] = None  # SHA-256 of vector data

    # RED TEAM FIX #4: Validators ensure dimension correctness
    @validator('stroke_dna', 'image_dna', 'temporal_dna')
    def validate_dimensions(cls, v):
        return validate_vector_dim(v, STYLE_VECTOR_DIM)


class IntentProfile(BaseModel):
    """Mind Layer - Emotional/narrative intent"""
    id: str = Field(default_factory=lambda: generate_id("intent"))
    session_id: Optional[str] = None
    artifact_id: Optional[str] = None

    # Emotional weighting (0.0 - 1.0 scale)
    emotional_register: Dict[str, float] = Field(
        default_factory=dict,
        description="e.g., {'joy': 0.8, 'melancholy': 0.4, 'chaos': 0.2}"
    )

    target_audience: Optional[str] = None
    constraints: List[str] = Field(
        default_factory=list,
        description="e.g., ['black & white', 'WCAG AA contrast']"
    )
    narrative_prompt: Optional[str] = None
    style_keywords: List[str] = Field(
        default_factory=list,
        description="e.g., ['brutalist', 'ethereal', 'organic']"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # RED TEAM MITIGATION: Extensible source field
    source: str = "user_prompt"
    # Valid values: "user_prompt" | "inferred" | "imported" |
    #               "system_generated" | "style_transfer" | "critic_adjusted"


class TelemetryChunk(BaseModel):
    """
    Muscle Layer - Stroke telemetry pointer (stored in Parquet)

    RED TEAM MITIGATION: Clarified row counting
    """
    id: str = Field(default_factory=lambda: generate_id("tel"))
    session_id: str
    artifact_id: Optional[str] = None

    # One Parquet file per session (avoids concurrency)
    parquet_path: str  # e.g., "data/telemetry/session_{id}.parquet"

    # RED TEAM MITIGATION: Clear semantics for row counting
    chunk_row_count: int  # Rows in THIS write operation
    total_session_rows: int  # Total rows in entire session file

    created_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: int = 1  # Future-proofing for schema evolution
