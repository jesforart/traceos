from fastapi import APIRouter, HTTPException
from typing import List
import logging

from drawing.models import Stroke, ProcessedStroke
from drawing.storage_instances import stroke_processor, stroke_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/drawing", tags=["drawing"])

@router.post("/strokes", response_model=ProcessedStroke)
async def save_stroke(stroke: Stroke):
    """Save a captured stroke."""
    try:
        logger.info(f"Saving stroke {stroke.id} with {len(stroke.points)} points")
        processed = stroke_processor.process_stroke(stroke)
        stroke_storage.store_stroke(processed)
        logger.debug(f"Stroke {stroke.id} metrics: length={processed.metrics.length:.2f}, avg_pressure={processed.metrics.avg_pressure:.2f}")
        return processed
    except Exception as e:
        logger.error(f"Failed to save stroke: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strokes", response_model=List[ProcessedStroke])
async def get_strokes():
    """Get all strokes from current session."""
    strokes = stroke_storage.get_session_strokes()
    logger.info(f"Retrieved {len(strokes)} strokes")
    return strokes

@router.get("/strokes/{stroke_id}", response_model=ProcessedStroke)
async def get_stroke(stroke_id: str):
    """Get specific stroke by ID."""
    stroke = stroke_storage.get_stroke(stroke_id)
    if not stroke:
        logger.warning(f"Stroke {stroke_id} not found")
        raise HTTPException(status_code=404, detail="Stroke not found")
    return stroke

@router.delete("/session")
async def clear_session():
    """Clear current drawing session."""
    stroke_storage.clear_session()
    logger.info("Session cleared")
    return {"message": "Session cleared"}

@router.get("/session/metrics")
async def get_session_metrics():
    """Get aggregated metrics for current session."""
    strokes = stroke_storage.get_session_strokes()

    if not strokes:
        return {
            "total_strokes": 0,
            "avg_pressure": 0,
            "avg_speed": 0,
            "total_length": 0
        }

    total_length = sum(s.metrics.length for s in strokes)
    avg_pressure = sum(s.metrics.avg_pressure for s in strokes) / len(strokes)
    avg_speed = sum(s.metrics.avg_speed for s in strokes) / len(strokes)

    logger.info(f"Session metrics: {len(strokes)} strokes, {total_length:.2f} total length")

    return {
        "total_strokes": len(strokes),
        "avg_pressure": avg_pressure,
        "avg_speed": avg_speed,
        "total_length": total_length
    }
