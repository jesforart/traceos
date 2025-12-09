"""
Dream Spark - Offline Consolidation Organ

Focus: Long-term compression of patterns into DNA lineage.
Tracks creative evolution across time.

@provenance traceos_sparks_v1
@organ dream
"""

import logging
from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata
from traceos.protocol.schemas import DeriveOutput, SparkReview, SparkComment

logger = logging.getLogger(__name__)


class DreamSpark(SparkBase):
    """
    Dream Spark tracks long-term creative evolution patterns.

    Observes DNA lineage growth and identifies seasonal patterns
    in the organism's creative development.
    """

    def _define_metadata(self) -> SparkMetadata:
        return SparkMetadata(
            name="Dream",
            organ_type="cognitive",
            description="Offline consolidation and long-term pattern tracking",
            version="1.0"
        )

    def evaluate(self, derivation: DeriveOutput) -> SparkReview:
        """
        Light evaluation: Comments on DNA growth rate.

        Dream doesn't judge individual derivations heavily,
        but tracks overall creative evolution.
        """
        # Import here to avoid circular imports
        from traceos.dna.store import DNAStore

        dna_store = DNAStore()
        lineage = dna_store.load_lineage()
        total = len(lineage)

        comments = []
        score = 0.7  # Baseline neutral

        if total == 0:
            comments.append(SparkComment(
                severity="low",
                message="No DNA lineage yet - nothing to consolidate"
            ))
        elif total < 5:
            comments.append(SparkComment(
                severity="info",
                message=f"Early DNA lineage: {total} snapshots"
            ))
            score += 0.1
        else:
            comments.append(SparkComment(
                severity="info",
                message=f"DNA lineage growing: {total} snapshots tracked"
            ))
            score += min(0.2, total / 50.0)  # Cap bonus at 0.2

        # Update Dream state (more lineage → more active)
        activation_level = min(1.0, 0.5 + total / 100.0)
        self.update_state(
            activation=activation_level,
            memory={"lineage_length": total},
            mood="observing"
        )

        # Determine status
        if score >= 0.85:
            status = "approve"
        elif score >= 0.65:
            status = "approve-with-changes"
        else:
            status = "reject"

        return SparkReview(
            spark="Dream",
            status=status,
            score=min(1.0, score),
            comments=comments
        )
