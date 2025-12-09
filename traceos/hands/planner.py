"""
Stroke Planner - Bridge between Mind and Body

Integrates:
- DNA (style memory)
- Gut (emotional state)
- Hands (physical capacity)

Produces biologically plausible stroke plans.

RED TEAM FIXES APPLIED:
- FIX 2: DNA alignment marked as inferred when no baseline
- FIX 3: Tremor clamping (max 3.0)
- FIX 4: Stroke ID uses timestamp (not points[0].time)
- FIX 5: Start == End validation

@provenance traceos_hands_v1
@organ somatic
"""

import logging
from typing import Tuple
from datetime import datetime

from traceos.sparks.registry import registry
from traceos.dna.store import DNAStore
from .schemas import StrokePlan, MotionParams
from .engine import MotionEngine

logger = logging.getLogger(__name__)


class StrokePlanner:
    """
    Integrates organism state to plan strokes.

    This is where mind meets body:
    - DNA -> style preferences
    - Gut -> emotional modulation
    - Hands -> physical constraints

    Output: Biologically plausible stroke trajectory
    """

    def __init__(self):
        self.engine = MotionEngine()
        self.dna_store = DNAStore()
        logger.info("StrokePlanner initialized")

    def plan_stroke(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        intent: str = "generic"
    ) -> StrokePlan:
        """
        Plan a stroke from current organism state.

        Args:
            start: (x, y) start position
            end: (x, y) end position
            intent: What this stroke aims to achieve

        Returns:
            StrokePlan with full trajectory and metadata
        """
        # FIX 5: Validate start != end
        if start == end:
            raise ValueError("Stroke start and end cannot be identical")

        logger.info(f"Planning stroke: {start} -> {end}, intent='{intent}'")

        # 1. Get Organ States
        hands = registry.get("Hands")
        gut = registry.get("Gut")

        fatigue = hands.state.fatigue if hands else 0.0
        mood = gut.state.mood if gut else "neutral"

        logger.debug(f"Organ states: Hands fatigue={fatigue:.2f}, Gut mood={mood}")

        # 2. Derive Motion Params from Context
        params = MotionParams()

        # Gut Influence (emotional modulation)
        if mood == "frustrated" or mood == "chaos":
            params.jitter_amount = 2.0  # Shaky when frustrated
            params.pressure_gain = 1.5  # Press harder
            params.velocity_base = 1.3  # Move faster (rushed)
            logger.debug("Applying 'frustrated' modulation")

        elif mood == "flow":
            params.smoothing_factor = 0.9  # Very smooth
            params.velocity_base = 1.2    # Confident speed
            params.jitter_amount = 0.2    # Minimal tremor
            logger.debug("Applying 'flow' modulation")

        elif mood == "uneasy":
            params.jitter_amount = 1.5   # More tremor
            params.velocity_base = 0.8   # Slower, hesitant
            logger.debug("Applying 'uneasy' modulation")

        # Fatigue Influence (physical constraint)
        # Tired hands shake more
        params.jitter_amount += (fatigue * 5.0)

        # FIX 3: Clamp tremor to prevent runaway
        params.jitter_amount = min(params.jitter_amount, 3.0)

        # DNA Influence (style memory)
        latest_dna = self.dna_store.get_latest_signature()
        dna_alignment = 0.0  # FIX 2: Default to 0.0 (not 0.9)
        dna_inferred = True

        if latest_dna:
            # Extract style preferences from DNA metrics
            if "gut_vibe_score" in latest_dna.metrics:
                vibe = latest_dna.metrics["gut_vibe_score"].value
                # High vibe = smoother strokes
                params.smoothing_factor = max(params.smoothing_factor, vibe * 0.5)

            dna_alignment = 0.9  # Assume high alignment when DNA exists
            dna_inferred = False
            logger.debug(f"DNA baseline: {latest_dna.signature_id}")

        # 3. Generate Trajectory
        points = self.engine.generate_trajectory(start, end, params)

        # FIX 4: Use timestamp for unique stroke ID (not points[0].time which is always 0.0)
        stroke_id = f"stroke_{int(datetime.utcnow().timestamp() * 1000)}"

        plan = StrokePlan(
            stroke_id=stroke_id,
            intent=intent,
            points=points,
            motion_params=params,
            dna_alignment=dna_alignment,
            metadata={
                "gut_mood": mood,
                "hands_fatigue": fatigue,
                "has_dna_baseline": latest_dna is not None,
                "dna_inferred": dna_inferred  # FIX 2: Mark if alignment is calculated or assumed
            }
        )

        logger.info(f"Stroke planned: {stroke_id}, {len(points)} points")
        return plan
