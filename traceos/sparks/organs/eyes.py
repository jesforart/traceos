"""
Eyes Spark - Visual Organ

Focus: Documentation, diagrams, visual clarity.

@provenance traceos_sparks_v1
@organ visual
"""

import logging
from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata
from traceos.protocol.schemas import DeriveOutput, SparkReview, SparkComment

logger = logging.getLogger(__name__)


class EyesSpark(SparkBase):
    """
    Eyes Spark evaluates visual clarity and documentation quality.

    Heuristics:
    - README.md presence
    - Documentation files
    - Visual assets (SVG, diagrams)
    """

    def _define_metadata(self) -> SparkMetadata:
        return SparkMetadata(
            name="Eyes",
            organ_type="visual",
            description="Visual perception and documentation clarity",
            version="1.0"
        )

    def evaluate(self, derivation: DeriveOutput) -> SparkReview:
        """Evaluate visual and documentation quality."""
        score = 0.6  # Baseline
        comments = []

        # Check for documentation
        doc_files = [
            f for f in derivation.files
            if any(ext in f.path.lower() for ext in ['.md', 'readme', 'doc'])
        ]

        if doc_files:
            comments.append(SparkComment(
                severity="info",
                message=f"Found {len(doc_files)} documentation files"
            ))
            score += 0.2
        else:
            comments.append(SparkComment(
                severity="low",
                message="No documentation files detected"
            ))

        # Check for visual assets
        visual_files = [
            f for f in derivation.files
            if any(ext in f.path.lower() for ext in ['.svg', '.png', 'diagram'])
        ]

        if visual_files:
            comments.append(SparkComment(
                severity="info",
                message=f"Contains {len(visual_files)} visual assets"
            ))
            score += 0.15

        # Update Eyes state
        activation = 0.7 if (doc_files or visual_files) else 0.4
        self.update_state(activation=activation)

        # Determine status
        if score >= 0.8:
            status = "approve"
        elif score >= 0.6:
            status = "approve-with-changes"
        else:
            status = "reject"

        return SparkReview(
            spark="Eyes",
            status=status,
            score=min(1.0, score),
            comments=comments
        )
