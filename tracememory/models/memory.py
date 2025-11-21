"""
Memory block models and data structures for MemAgent.

This module defines the core memory structures:
- MemoryBlock: Complete session memory state
- AssetState: Current asset state (SVG/GLTF/etc)
- DesignDNA: Style characteristics and constraints
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import hashlib
import json


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
