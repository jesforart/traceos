"""
Renderer API Routes

Provides backend endpoints to:
- Plan a stroke using Hands (StrokePlanner)
- Render that stroke onto a Canvas
- Save the composite image to disk

This is a backend 'imagination' path, not the realtime UI renderer.

@provenance traceos_renderer_v1
@organ visual
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from traceos.renderer.canvas import Canvas
from traceos.hands.planner import StrokePlanner

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory global canvas and planner for the current process.
# In a multi-user or multi-session context, this would be session-scoped.
planner = StrokePlanner()
global_canvas = Canvas()


@router.post("/stroke")
async def render_stroke_api(
    start_x: float = Query(..., description="Start X coordinate"),
    start_y: float = Query(..., description="Start Y coordinate"),
    end_x: float = Query(..., description="End X coordinate"),
    end_y: float = Query(..., description="End Y coordinate"),
    intent: str = Query("visual_test", description="Stroke intent")
):
    """
    Plan AND render a stroke.

    Pipeline:
    - Hands: StrokePlanner generates a biologically plausible StrokePlan
    - Renderer: Canvas renders the stroke onto a new layer
    - Output: Composite PNG saved under ./data/artifacts/visuals/

    Returns path to the generated image and stroke metadata.
    """
    try:
        # 1. Plan with Hands
        plan = planner.plan_stroke((start_x, start_y), (end_x, end_y), intent)

        # 2. Render with Canvas
        layer = global_canvas.add_layer(f"layer_{plan.stroke_id}")
        global_canvas.render_stroke(layer, plan)

        # 3. Save output PNG
        output_dir = Path("./data/artifacts/visuals")
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{plan.stroke_id}.png"
        path = output_dir / filename

        final_image = global_canvas.composite()
        final_image.save(path)

        logger.info(f"Rendered stroke {plan.stroke_id} to {path}")

        return {
            "status": "rendered",
            "stroke_id": plan.stroke_id,
            "image_path": str(path),
            "points_rendered": len(plan.points)
        }
    except ValueError as e:
        # Start == End validation
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Stroke rendering failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/canvas/info")
async def canvas_info():
    """Get information about the current canvas state."""
    return {
        "width": global_canvas.width,
        "height": global_canvas.height,
        "layer_count": len(global_canvas.layers),
        "layers": [{"name": l.name, "visible": l.is_visible} for l in global_canvas.layers]
    }


@router.post("/canvas/reset")
async def reset_canvas():
    """Reset the canvas to a fresh state."""
    global global_canvas
    global_canvas = Canvas()
    logger.info("Canvas reset to fresh state")
    return {"status": "reset", "width": global_canvas.width, "height": global_canvas.height}
