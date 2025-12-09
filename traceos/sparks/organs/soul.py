"""
Soul Spark - Identity Organ

Focus: Provenance, brand alignment, identity coherence.
Phase 4: Now checks DNA baseline for identity alignment.

@provenance traceos_sparks_v1
@organ identity
"""

import logging
from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata
from traceos.protocol.schemas import DeriveOutput, SparkReview, SparkComment

logger = logging.getLogger(__name__)


class SoulSpark(SparkBase):
    """
    Soul Spark evaluates identity coherence and provenance tracking.

    Heuristics:
    - Provenance node validation
    - TraceOS brand alignment
    - Identity markers in code
    - DNA baseline presence (Phase 4)
    """

    def _define_metadata(self) -> SparkMetadata:
        return SparkMetadata(
            name="Soul",
            organ_type="identity",
            description="Self-model, identity, and provenance guardian",
            version="1.0"
        )

    def evaluate(self, derivation: DeriveOutput) -> SparkReview:
        """
        Evaluate identity coherence and provenance.

        Phase 4: Now checks DNA baseline for identity alignment.
        """
        score = 0.8  # Baseline positive (Soul is optimistic)
        comments = []

        # Provenance checks
        if derivation.provenance and derivation.provenance.node_id:
            comments.append(SparkComment(
                severity="info",
                message=f"Provenance tracked: {derivation.provenance.node_id}"
            ))
            score += 0.1
        else:
            comments.append(SparkComment(
                severity="high",
                message="Missing provenance node - identity traceability compromised"
            ))
            score -= 0.3

        # Check for TraceOS branding in notes
        notes_lower = derivation.notes.lower()
        identity_markers = ["traceos", "spark", "organism", "provenance", "dna"]
        found_markers = [m for m in identity_markers if m in notes_lower]

        if found_markers:
            comments.append(SparkComment(
                severity="info",
                message=f"Strong identity alignment: {', '.join(found_markers)}"
            ))
            score += 0.05

        # DNA alignment check (NEW FOR PHASE 4)
        # Import here to avoid circular imports
        from traceos.dna.store import DNAStore
        dna_store = DNAStore()
        latest_sig = dna_store.get_latest_signature()

        if latest_sig:
            comments.append(SparkComment(
                severity="info",
                message=f"Creative DNA baseline present (latest={latest_sig.signature_id})"
            ))
            score += 0.05
        else:
            comments.append(SparkComment(
                severity="low",
                message="No creative DNA baseline found yet"
            ))

        # Update Soul state
        identity_strength = score
        self.update_state(
            activation=0.95,
            memory={"identity_strength": identity_strength}
        )

        # Determine status
        if score >= 0.85:
            status = "approve"
        elif score >= 0.65:
            status = "approve-with-changes"
        else:
            status = "reject"

        return SparkReview(
            spark="Soul",
            status=status,
            score=min(1.0, score),
            comments=comments
        )
