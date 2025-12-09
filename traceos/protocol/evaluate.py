"""
Evaluate Handler - Multi-Spark review orchestration.

NOTE: This is currently a STUB implementation.
Real evaluation requires trained Sparks (Phase 2+).

@provenance traceos_protocol_v1
@organ kernel
"""

import logging
from typing import List, Optional

from .schemas import (
    EvaluateOutput,
    SparkReview,
    SparkComment,
    DeriveOutput
)
from .persistence import ProtocolStorage

logger = logging.getLogger(__name__)


class EvaluateHandler:
    """
    Orchestrates multi-Spark evaluation of derived implementations.

    CURRENT STATUS: Stub implementation with mock reviews
    FUTURE: Will call real Spark organs (Brain, Gut, Eyes, Soul)

    The four reviewing Sparks:
    - Brain: Logic, correctness, patterns
    - Gut: UX, vibe, "does this feel like TraceOS?"
    - Eyes: Visuals, diagrams, notebook clarity
    - Soul: Coherence with TraceOS identity & values
    """

    def __init__(self, storage: ProtocolStorage):
        self.storage = storage

    def evaluate(self, derivation: DeriveOutput) -> EvaluateOutput:
        """
        Run multi-Spark evaluation on derived implementation.

        STUB IMPLEMENTATION: Generates mock reviews.

        TODO (Phase 2+):
        1. Call real Brain organ API
        2. Call real Gut organ API
        3. Call real Eyes organ API
        4. Call real Soul organ API

        Args:
            derivation: Previously saved derivation output

        Returns:
            EvaluateOutput with reviews from all Sparks
        """
        logger.info(f"Evaluating derivation: {derivation.derive_id}")
        logger.warning("Using STUB evaluation - no real Spark reviews yet")

        reviews: List[SparkReview] = []

        # Stub Spark Reviews
        reviews.append(self._stub_brain_review(derivation))
        reviews.append(self._stub_gut_review(derivation))
        reviews.append(self._stub_eyes_review(derivation))
        reviews.append(self._stub_soul_review(derivation))

        # Determine overall status
        statuses = [r.status for r in reviews]
        if "reject" in statuses:
            overall = "rejected"
        elif "approve-with-changes" in statuses:
            overall = "needs-changes"
        else:
            overall = "approved"

        # Create output
        output = EvaluateOutput(
            intent_id=derivation.intent_id,
            derive_id=derivation.derive_id,
            reviews=reviews,
            overall_status=overall
        )

        # Persist evaluation
        self.storage.save_evaluation(output)

        logger.info(f"Evaluation complete: {overall}")

        return output

    def get_evaluation(self, derive_id: str) -> Optional[EvaluateOutput]:
        """Load existing evaluation by derive ID."""
        return self.storage.load_evaluation(derive_id)

    # ============================
    # STUB SPARK REVIEWS
    # ============================

    def _stub_brain_review(self, derivation: DeriveOutput) -> SparkReview:
        """
        STUB: Brain Spark review.

        TODO (Phase 2+): Call real Brain organ endpoint
        """
        return SparkReview(
            spark="Brain",
            status="approve",
            score=0.85,
            comments=[
                SparkComment(
                    severity="info",
                    message="[STUB] Architecture follows TraceOS patterns"
                )
            ]
        )

    def _stub_gut_review(self, derivation: DeriveOutput) -> SparkReview:
        """
        STUB: Gut Spark review.

        TODO (Phase 2+): Call real Gut organ endpoint
        """
        return SparkReview(
            spark="Gut",
            status="approve",
            score=0.90,
            comments=[
                SparkComment(
                    severity="info",
                    message="[STUB] Naming aligns with TraceOS metaphors"
                )
            ]
        )

    def _stub_eyes_review(self, derivation: DeriveOutput) -> SparkReview:
        """
        STUB: Eyes Spark review.

        TODO (Phase 2+): Call real Eyes organ endpoint
        """
        return SparkReview(
            spark="Eyes",
            status="approve",
            score=0.88,
            comments=[
                SparkComment(
                    severity="info",
                    message="[STUB] Visual clarity acceptable"
                )
            ]
        )

    def _stub_soul_review(self, derivation: DeriveOutput) -> SparkReview:
        """
        STUB: Soul Spark review.

        TODO (Phase 2+): Call real Soul organ endpoint
        """
        return SparkReview(
            spark="Soul",
            status="approve",
            score=0.92,
            comments=[
                SparkComment(
                    severity="info",
                    message="[STUB] Aligns with TraceOS values"
                )
            ]
        )
