from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from drawing.semantic_models import (
    SemanticElement,
    CreateSemanticElementRequest,
    AutoDetectRequest,
    UpdateSemanticElementRequest,
    BoundingBox
)
from drawing.storage_instances import auto_detector, semantic_storage, stroke_storage

router = APIRouter(prefix="/api/semantic", tags=["semantic"])

@router.post("/elements", response_model=SemanticElement)
async def create_semantic_element(request: CreateSemanticElementRequest):
    """Create semantic element from stroke selection."""
    try:
        # Get strokes to calculate bounding box
        strokes = []
        for sid in request.stroke_ids:
            processed_stroke = stroke_storage.get_stroke(sid)
            if processed_stroke:
                strokes.append(processed_stroke.stroke)

        if not strokes:
            raise HTTPException(status_code=404, detail="Strokes not found")

        # Calculate bounding box
        all_points = []
        for stroke in strokes:
            all_points.extend([(p.x, p.y) for p in stroke.points])

        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]

        element = SemanticElement(
            id=f"elem_{int(datetime.now().timestamp() * 1000)}",
            label=request.label,
            stroke_ids=request.stroke_ids,
            bounding_box=BoundingBox(
                min_x=min(xs),
                min_y=min(ys),
                max_x=max(xs),
                max_y=max(ys)
            ),
            auto_detected=False,
            created_at=int(datetime.now().timestamp() * 1000)
        )

        semantic_storage.store_element(element)
        return element

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/elements", response_model=List[SemanticElement])
async def get_semantic_elements():
    """Get all semantic elements."""
    return semantic_storage.get_all_elements()

@router.get("/elements/{element_id}", response_model=SemanticElement)
async def get_semantic_element(element_id: str):
    """Get specific semantic element."""
    element = semantic_storage.get_element(element_id)
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    return element

@router.patch("/elements/{element_id}")
async def update_semantic_element(element_id: str, request: UpdateSemanticElementRequest):
    """Update semantic element label."""
    element = semantic_storage.get_element(element_id)
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    element.label = request.label
    semantic_storage.store_element(element)
    return element

@router.delete("/elements/{element_id}")
async def delete_semantic_element(element_id: str):
    """Delete semantic element."""
    semantic_storage.delete_element(element_id)
    return {"message": "Element deleted"}

@router.post("/auto-detect", response_model=List[SemanticElement])
async def auto_detect_elements(request: AutoDetectRequest):
    """Auto-detect semantic elements from strokes."""
    try:
        # Get strokes
        if request.stroke_ids:
            strokes = []
            for sid in request.stroke_ids:
                processed_stroke = stroke_storage.get_stroke(sid)
                if processed_stroke:
                    strokes.append(processed_stroke.stroke)
        else:
            # Use all session strokes
            processed_strokes = stroke_storage.get_session_strokes()
            strokes = [ps.stroke for ps in processed_strokes]

        if not strokes:
            return []

        # Detect elements
        elements = auto_detector.detect_face_elements(strokes)

        # Store detected elements
        for element in elements:
            semantic_storage.store_element(element)

        return elements

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session")
async def clear_semantic_session():
    """Clear all semantic elements."""
    semantic_storage.clear_all()
    return {"message": "Semantic elements cleared"}
