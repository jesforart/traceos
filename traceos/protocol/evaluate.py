"""
Evaluate Handler - Multi-Spark review orchestration.

NOW USES REAL SPARKS instead of stubs!

@provenance traceos_protocol_v1
@organ kernel
"""

import logging
from typing import List, Optional

from .schemas import (
    EvaluateOutput,
    DeriveOutput
)
from .persistence import ProtocolStorage

logger = logging.getLogger(__name__)


class EvaluateHandler:
    """
    Orchestrates multi-Spark evaluation using REAL Spark organs.

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

        REAL IMPLEMENTATION: Calls actual Spark organs!

        Args:
            derivation: Previously saved derivation output

        Returns:
            EvaluateOutput with reviews from all Sparks
        """
        # Import here to avoid circular imports
        from traceos.sparks import registry as spark_registry

        logger.info(f"Evaluating derivation: {derivation.derive_id}")
        logger.info("Using REAL Sparks (Brain, Gut, Eyes, Soul)")

        reviews = []

        # Get reviews from all registered Sparks
        for spark in spark_registry.get_all():
            try:
                review = spark.evaluate(derivation)
                reviews.append(review)
                logger.debug(f"{spark.metadata.name}: {review.status} (score: {review.score:.2f})")
            except Exception as e:
                logger.error(f"Spark {spark.metadata.name} evaluation failed: {e}")

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
        logger.info(f"Spark states persisted to data/sparks/")

        return output

    def get_evaluation(self, derive_id: str) -> Optional[EvaluateOutput]:
        """Load existing evaluation by derive ID."""
        return self.storage.load_evaluation(derive_id)
