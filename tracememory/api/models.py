"""
API request/response models for MemAgent service
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# ============================================================
# HEALTH & VERSION
# ============================================================

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    timestamp: datetime
    components: Dict[str, str]

class VersionResponse(BaseModel):
    api_version: str
    service_version: str
    hf_model: Optional[str] = None

# ============================================================
# SESSION
# ============================================================

class SessionInitRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Trace session ID")
    intent: str = Field(..., min_length=1, description="Design intent/goal")
    created_by: str = Field(default="user")
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not v.startswith('session_'):
            raise ValueError('session_id must start with "session_"')
        return v

class SessionInitResponse(BaseModel):
    status: str = "ok"
    memory_block_id: str
    session_id: str

# ============================================================
# MEMORY BLOCK
# ============================================================

class AssetState(BaseModel):
    """Asset state within memory block"""
    type: str = Field(..., description="svg | gltf | png")
    data: str = Field(..., description="Asset content")
    uri: Optional[str] = None
    created_at: datetime
    thumbnail: Optional[str] = None

class DesignDNA(BaseModel):
    """Design DNA / Style characteristics"""
    style_embedding_id: Optional[str] = None
    distance_from_root: float = 0.0
    distance_band: Dict[str, float] = {"min": 0.15, "max": 0.55}
    aesthetic_profile: Dict[str, Any] = {}
    constraints: Dict[str, Any] = {}

class MemoryBlockResponse(BaseModel):
    """Complete session memory state"""
    session_id: str
    memory_block_id: str
    last_updated: datetime
    
    # Compressed narrative
    summary: str = Field(..., description="HF model compressed summary", max_length=2048)
    
    # Structured state
    last_asset: Optional[AssetState] = None
    active_modifiers: Dict[str, float] = {}
    design_dna: Optional[DesignDNA] = None
    
    # Context
    user_notes: List[str] = []
    pending_tasks: List[Dict[str, Any]] = []
    
    # Provenance
    provenance_chain: List[str] = []
    
    # Metadata
    event_count: int = 0
    compression_version: str = "1.0"

# ============================================================
# COMPRESSION
# ============================================================

class CompressionResult(BaseModel):
    """Result of compression operation"""
    summary: str
    key_decisions: List[str] = []
    active_modifiers: Dict[str, float] = {}
    user_preferences: List[str] = []
    design_intent: str = ""
    compressed_at: datetime
    
    # Metrics
    events_processed: int
    tokens_in: int
    tokens_out: int
    compression_ratio: float

class CompressionResponse(BaseModel):
    status: str = "ok"
    compression_result: CompressionResult
    events_processed: int
    tokens_in: int
    tokens_out: int
    compression_ratio: float

# ============================================================
# VARIATIONS
# ============================================================

class VariationRequest(BaseModel):
    modifier: str = Field(..., description="Modifier name (e.g., stroke_weight, hue_shift)")
    value: float = Field(..., ge=0.0, le=1.0, description="Normalized value 0.0-1.0")

    @validator('modifier')
    def validate_modifier(cls, v):
        # All 12 modifiers from svg_modifiers.py
        valid = [
            'stroke_weight', 'fill_opacity', 'hue_shift', 'scale', 'rotate',
            'brightness', 'saturation', 'contrast', 'blur', 'x_offset', 'y_offset', 'skew'
        ]
        if v not in valid:
            raise ValueError(f'modifier must be one of: {", ".join(valid)}')
        return v

class VariationResponse(BaseModel):
    status: str = "ok"
    session_id: str
    variant_id: str
    modifier: str
    value: float
    svg_data: str
    metadata: Dict[str, Any]

class BatchVariationsRequest(BaseModel):
    modifiers: Dict[str, float] = Field(
        ...,
        description="Dictionary of {modifier_name: value}",
        min_items=1,
        max_items=12
    )

    @validator('modifiers')
    def validate_modifiers(cls, v):
        valid = [
            'stroke_weight', 'fill_opacity', 'hue_shift', 'scale', 'rotate',
            'brightness', 'saturation', 'contrast', 'blur', 'x_offset', 'y_offset', 'skew'
        ]
        for modifier, value in v.items():
            if modifier not in valid:
                raise ValueError(f'modifier "{modifier}" not valid. Must be one of: {", ".join(valid)}')
            if not (0.0 <= value <= 1.0):
                raise ValueError(f'value for "{modifier}" must be in range [0.0, 1.0], got {value}')
        return v

class BatchVariationsResponse(BaseModel):
    status: str = "ok"
    session_id: str
    variant_id: str
    modifiers_applied: List[Dict[str, Any]]
    svg_data: str
    metadata: Dict[str, Any]

class AssetResponse(BaseModel):
    asset: Dict[str, Any]

class AssetUploadRequest(BaseModel):
    type: str = Field(..., description="Asset type: svg | png | gltf")
    data: str = Field(..., description="Asset content (SVG string or base64 for binary)")
    uri: Optional[str] = Field(None, description="Optional custom URI")

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['svg', 'png', 'gltf']
        if v not in valid_types:
            raise ValueError(f'type must be one of: {", ".join(valid_types)}')
        return v

class AssetUploadResponse(BaseModel):
    status: str = "ok"
    asset: Dict[str, Any]

# ============================================================
# SCHEMA & MEMORY
# ============================================================

class SchemaEmbedRequest(BaseModel):
    session_id: str
    schema_id: str
    design_dna: Dict[str, Any]

class EmbedResponse(BaseModel):
    status: str = "ok"
    schema_id: str

class NoteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    timestamp: Optional[datetime] = None

class NoteResponse(BaseModel):
    status: str = "ok"

class SearchResponse(BaseModel):
    results: List[MemoryBlockResponse]
    query: str
    count: int
