"""
Gut Spark - Affective Organ

Focus: UX, vibe, naming, emotional resonance.

@provenance traceos_sparks_v1
@organ affective
"""

import logging
from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata
from traceos.protocol.schemas import DeriveOutput, SparkReview, SparkComment

logger = logging.getLogger(__name__)


class GutSpark(SparkBase):
    """
    Gut Spark evaluates emotional resonance and UX quality.

    Heuristics:
    - Intent tag analysis (quantum = excitement)
    - Keyword detection (stub, hack, todo = unease)
    - Naming quality
    """

    def _define_metadata(self) -> SparkMetadata:
        return SparkMetadata(
            name="Gut",
            organ_type="affective",
            description="Intuition, taste, and emotional resonance",
            version="1.0"
        )

    def evaluate(self, derivation: DeriveOutput) -> SparkReview:
        """Evaluate emotional and UX quality."""
        score = 0.7  # Baseline positive
        comments = []
        mood = "neutral"

        # Check derivation notes for concerning keywords
        notes_lower = derivation.notes.lower()

        concerning_keywords = ["stub", "hack", "todo", "fixme", "broken"]
        found_concerns = [kw for kw in concerning_keywords if kw in notes_lower]

        if found_concerns:
            comments.append(SparkComment(
                severity="medium",
                message=f"Detected technical debt markers: {', '.join(found_concerns)}"
            ))
            score -= 0.1 * len(found_concerns)
            mood = "uneasy"

        # Check for positive signals
        positive_keywords = ["quantum", "energy", "landscape", "dna", "spark"]
        found_positive = [kw for kw in positive_keywords if kw in notes_lower]

        if found_positive:
            comments.append(SparkComment(
                severity="info",
                message=f"Resonates with TraceOS vision: {', '.join(found_positive)}"
            ))
            score += 0.1
            mood = "excited"

        # Update Gut state
        self.update_state(
            activation=0.9,  # Gut is highly active
            mood=mood
        )

        # Determine status
        if score >= 0.8:
            status = "approve"
        elif score >= 0.6:
            status = "approve-with-changes"
        else:
            status = "reject"

        return SparkReview(
            spark="Gut",
            status=status,
            score=min(1.0, max(0.0, score)),
            comments=comments
        )
