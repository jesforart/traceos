from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class BoundingBox(BaseModel):
    """Bounding box for semantic element."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float

class SemanticElement(BaseModel):
    """Semantic element - labeled collection of strokes."""
    id: str
    label: str
    stroke_ids: List[str]
    bounding_box: BoundingBox
    confidence: Optional[float] = None
    auto_detected: bool = False
    created_at: int

class CreateSemanticElementRequest(BaseModel):
    """Request to create semantic element."""
    label: str
    stroke_ids: List[str]

class UpdateSemanticElementRequest(BaseModel):
    """Request to update semantic element."""
    label: str

class AutoDetectRequest(BaseModel):
    """Request to auto-detect semantic elements."""
    drawing_id: Optional[str] = None
    stroke_ids: Optional[List[str]] = None

# Available face tags
FACE_TAGS = [
    "left_eyebrow", "right_eyebrow",
    "left_eye", "right_eye",
    "nose", "mouth", "jaw",
    "left_ear", "right_ear",
    "hair", "outline", "other"
]
