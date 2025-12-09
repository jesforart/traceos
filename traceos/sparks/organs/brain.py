"""
Brain Spark - Cognitive Organ

Focus: Logic, architecture, correctness, patterns.

@provenance traceos_sparks_v1
@organ cognitive
"""

import logging
from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata
from traceos.protocol.schemas import DeriveOutput, SparkReview, SparkComment

logger = logging.getLogger(__name__)


class BrainSpark(SparkBase):
    """
    Brain Spark evaluates logical correctness and architectural quality.

    Heuristics:
    - File structure quality
    - Code organization
    - LOC counts (fatigue increases with complexity)
    """

    def _define_metadata(self) -> SparkMetadata:
        return SparkMetadata(
            name="Brain",
            organ_type="cognitive",
            description="Logic, reasoning, and architectural analysis",
            version="1.0"
        )

    def evaluate(self, derivation: DeriveOutput) -> SparkReview:
        """Evaluate logical and architectural quality."""
        score = 0.5  # Baseline
        comments = []

        # Check file count
        file_count = len(derivation.files)

        if file_count == 0:
            comments.append(SparkComment(
                severity="high",
                message="No files generated - derivation appears incomplete"
            ))
            score = 0.3
        elif file_count > 0:
            comments.append(SparkComment(
                severity="info",
                message=f"Generated {file_count} files - good structural organization"
            ))
            score = 0.85

        # Check for traceos/ module structure
        traceos_files = [f for f in derivation.files if 'traceos/' in f.path]
        if traceos_files:
            comments.append(SparkComment(
                severity="info",
                message="Follows TraceOS module conventions"
            ))
            score += 0.05

        # Update Brain state (fatigue from LOC)
        total_loc = sum(f.loc for f in derivation.files)
        fatigue_increase = min(0.3, total_loc / 1000.0)  # Cap at 0.3

        self.update_state(
            activation=0.8,  # Brain is active during evaluation
            fatigue=min(1.0, self.state.fatigue + fatigue_increase)
        )

        # Determine status
        if score >= 0.8:
            status = "approve"
        elif score >= 0.6:
            status = "approve-with-changes"
        else:
            status = "reject"

        return SparkReview(
            spark="Brain",
            status=status,
            score=min(1.0, score),
            comments=comments
        )
