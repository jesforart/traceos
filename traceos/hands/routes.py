"""
Hands API Routes

Endpoints for stroke planning and Hands organ status.

@provenance traceos_hands_v1
@organ somatic
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from traceos.sparks.registry import registry
from .planner import StrokePlanner
from .schemas import StrokePlan, HandsStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/hands", tags=["hands"])

# Initialize planner (singleton)
stroke_planner = StrokePlanner()


@router.post("/stroke", response_model=StrokePlan)
async def plan_stroke(
    start_x: float = Query(..., description="Start X coordinate"),
    start_y: float = Query(..., description="Start Y coordinate"),
    end_x: float = Query(..., description="End X coordinate"),
    end_y: float = Query(..., description="End Y coordinate"),
    intent: Optional[str] = Query("generic", description="Stroke intent")
) -> StrokePlan:
    """
    Plan a stroke from current organism state.

    Integrates:
    - DNA style baseline
    - Gut emotional state
    - Hands fatigue level

    Returns a complete trajectory ready for execution.
    """
    try:
        plan = stroke_planner.plan_stroke(
            start=(start_x, start_y),
            end=(end_x, end_y),
            intent=intent
        )

        # Update Hands state (track usage)
        hands = registry.get("Hands")
        if hands:
            # Increment fatigue slightly per stroke (FIX 6: reduced from 0.05)
            new_fatigue = min(1.0, hands.state.fatigue + 0.02)
            hands.update_state(
                activation=0.9,
                fatigue=new_fatigue
            )

        return plan

    except ValueError as e:
        # FIX 5: Start == End validation error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Stroke planning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=HandsStatus)
async def get_hands_status() -> HandsStatus:
    """
    Get current Hands organ status.

    Returns fatigue, capacity, and activation levels.
    """
    hands = registry.get("Hands")

    if not hands:
        return HandsStatus(
            fatigue=0.0,
            capacity=1.0,
            stroke_count=0,
            activation=0.0
        )

    return HandsStatus(
        fatigue=hands.state.fatigue,
        capacity=hands.get_current_capacity(),
        stroke_count=getattr(hands, '_stroke_count', 0),
        activation=hands.state.activation
    )


@router.post("/rest")
async def rest_hands() -> dict:
    """
    Rest the Hands organ (reduce fatigue).

    Call this to simulate rest periods.
    """
    hands = registry.get("Hands")

    if not hands:
        return {"status": "no_hands_registered", "fatigue": 0.0}

    hands.rest()

    return {
        "status": "rested",
        "fatigue": hands.state.fatigue,
        "capacity": hands.get_current_capacity()
    }


@router.post("/reset")
async def reset_hands() -> dict:
    """
    Fully reset Hands state (zero fatigue).

    Use sparingly - this is like a full night's sleep.
    """
    hands = registry.get("Hands")

    if not hands:
        return {"status": "no_hands_registered"}

    hands.update_state(
        fatigue=0.0,
        activation=0.0
    )

    return {
        "status": "reset",
        "fatigue": 0.0,
        "capacity": 1.0
    }
