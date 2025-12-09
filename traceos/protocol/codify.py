"""
Codify Handler - Captures learnings into design DNA.

@provenance traceos_protocol_v1
@organ kernel
"""

import logging
from datetime import datetime
from typing import Optional

from .schemas import CodifyOutput, EvaluateOutput
from .persistence import ProtocolStorage

logger = logging.getLogger(__name__)


class CodifyHandler:
    """
    Captures implementation learnings into TraceOS design DNA.

    This updates the Double DNA Engine with patterns discovered
    during implementation, creating compounding knowledge.

    TODO (Phase 2+): Wire to real Double DNA Engine
    """

    def __init__(self, storage: ProtocolStorage):
        self.storage = storage

    def codify(self, evaluation: EvaluateOutput) -> CodifyOutput:
        """
        Extract patterns and lessons from evaluation.

        Args:
            evaluation: Previously saved evaluation output

        Returns:
            CodifyOutput with captured learnings
        """
        logger.info(f"Codifying learnings for: {evaluation.derive_id}")

        patterns = []
        lessons = []

        # Extract patterns from Spark reviews
        for review in evaluation.reviews:
            for comment in review.comments:
                if "pattern" in comment.message.lower():
                    patterns.append(comment.message)
                else:
                    lessons.append(f"[{review.spark}] {comment.message}")

        # Create codified output
        output = CodifyOutput(
            intent_id=evaluation.intent_id,
            derive_id=evaluation.derive_id,
            codified={
                "patterns": patterns,
                "lessons": lessons,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Persist codification
        self.storage.save_codification(output)

        # TODO (Phase 2+): Store in Double DNA Engine

        logger.info(f"Captured {len(patterns)} patterns, {len(lessons)} lessons")

        return output

    def get_codification(self, derive_id: str) -> Optional[CodifyOutput]:
        """Load existing codification by derive ID."""
        return self.storage.load_codification(derive_id)
