"""
Hands Spark - Somatic Organ

Tracks motor capability, fatigue, and execution state.

Unlike cognitive Sparks, Hands doesn't judge work quality -
it tracks the physical capacity to execute strokes.

RED TEAM FIXES APPLIED:
- FIX 1: organ_type = "somatic" (not "visual")
- FIX 6: Fatigue increment reduced to 0.02 (was 0.05)

@provenance traceos_sparks_v1
@organ somatic
"""

import logging
from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata
from traceos.protocol.schemas import DeriveOutput, SparkReview, SparkComment

logger = logging.getLogger(__name__)


class HandsSpark(SparkBase):
    """
    Hands Spark - Motor control organ.

    Tracks:
    - Fatigue (execution capacity)
    - Activation (readiness to act)
    - Stroke count (usage statistics)
    """

    def _define_metadata(self) -> SparkMetadata:
        return SparkMetadata(
            name="Hands",
            organ_type="somatic",  # FIX 1: Correct classification
            description="Somatic expression and motor control",
            version="1.0"
        )

    def evaluate(self, derivation: DeriveOutput) -> SparkReview:
        """
        Light evaluation: Hands checks if it can execute.

        Hands doesn't judge quality (that's Brain/Gut/Eyes/Soul's job).
        Hands only reports capability.
        """
        score = 0.8
        comments = []

        # Check current capacity
        capacity = self.get_current_capacity()

        if capacity < 0.3:
            comments.append(SparkComment(
                severity="medium",
                message=f"Hands fatigued (capacity: {capacity:.2f}) - may affect execution quality"
            ))
            score = 0.6
        else:
            comments.append(SparkComment(
                severity="info",
                message=f"Hands ready (capacity: {capacity:.2f})"
            ))

        # FIX 6: Reduced fatigue increment (was 0.05, now 0.02)
        # Prevents hands from becoming useless after 20 strokes
        self.update_state(
            activation=0.8,
            fatigue=min(1.0, self.state.fatigue + 0.02)
        )

        status = "approve" if score >= 0.7 else "approve-with-changes"

        return SparkReview(
            spark="Hands",
            status=status,
            score=score,
            comments=comments
        )

    def get_current_capacity(self) -> float:
        """
        Return 0.0-1.0 representing how 'fresh' the hands are.

        High fatigue = low capacity.
        """
        return max(0.1, 1.0 - self.state.fatigue)

    def rest(self) -> None:
        """Reduce fatigue (simulate rest)."""
        self.update_state(
            fatigue=max(0.0, self.state.fatigue - 0.2)
        )
        logger.info(f"Hands rested, new fatigue: {self.state.fatigue:.2f}")
