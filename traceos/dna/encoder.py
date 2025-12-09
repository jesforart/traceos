"""
Creative DNA Encoder

Turns DeriveOutput + EvaluateOutput into StyleSignatures.

Extracts features that define creative identity:
- Structural complexity (Brain)
- Emotional resonance (Gut)
- Visual clarity (Eyes)
- Identity alignment (Soul)

@provenance traceos_dna_v1
@organ identity
"""

import logging
from datetime import datetime
from typing import Dict

from traceos.protocol.schemas import DeriveOutput, EvaluateOutput
from .schemas import StyleSignature, StyleMetric
from .alignment import aggregate_metric_vector

logger = logging.getLogger(__name__)


class DNAEncoder:
    """
    Encodes TraceOS derivations and Spark reviews into StyleSignatures.

    This is the organism's memory formation process - deciding which
    aspects of work define creative identity.
    """

    @staticmethod
    def from_evaluation(
        intent_id: str,
        derivation: DeriveOutput,
        evaluation: EvaluateOutput
    ) -> StyleSignature:
        """
        Create a StyleSignature from derivation + evaluation.

        Args:
            intent_id: Intent that spawned this work
            derivation: The derived implementation
            evaluation: Spark reviews of the work

        Returns:
            StyleSignature encoding the creative DNA
        """
        metrics: Dict[str, StyleMetric] = {}

        # Structural metrics from derivation
        file_count = len(derivation.files)
        total_loc = sum(f.loc for f in derivation.files)

        metrics["file_structure_complexity"] = StyleMetric(
            name="file_structure_complexity",
            value=float(file_count),
            weight=1.0,
            description="Number of files in derivation"
        )

        metrics["loc_volume"] = StyleMetric(
            name="loc_volume",
            value=float(total_loc),
            weight=0.5,
            description="Total lines of code/text"
        )

        # Extract per-Spark scores from evaluation
        spark_scores: Dict[str, float] = {}
        for review in evaluation.reviews:
            spark_scores[review.spark] = review.score

        # Brain: Architectural quality
        if "Brain" in spark_scores:
            metrics["brain_score"] = StyleMetric(
                name="brain_score",
                value=spark_scores["Brain"],
                weight=1.2,
                description="Architectural/logic quality"
            )

        # Gut: Emotional resonance
        if "Gut" in spark_scores:
            metrics["gut_vibe_score"] = StyleMetric(
                name="gut_vibe_score",
                value=spark_scores["Gut"],
                weight=1.5,
                description="Emotional/taste resonance"
            )

        # Eyes: Visual clarity
        if "Eyes" in spark_scores:
            metrics["eyes_clarity_score"] = StyleMetric(
                name="eyes_clarity_score",
                value=spark_scores["Eyes"],
                weight=1.0,
                description="Documentation and visual clarity"
            )

        # Soul: Identity alignment
        if "Soul" in spark_scores:
            metrics["soul_identity_score"] = StyleMetric(
                name="soul_identity_score",
                value=spark_scores["Soul"],
                weight=2.0,
                description="Identity & provenance alignment"
            )

        # Dream: Long-term consolidation (if present)
        if "Dream" in spark_scores:
            metrics["dream_consolidation_score"] = StyleMetric(
                name="dream_consolidation_score",
                value=spark_scores["Dream"],
                weight=0.8,
                description="Long-term pattern recognition"
            )

        # Provenance tracking
        has_provenance = 1.0 if derivation.provenance and derivation.provenance.node_id else 0.0
        metrics["provenance_tracked"] = StyleMetric(
            name="provenance_tracked",
            value=has_provenance,
            weight=2.0,
            description="Full provenance tracking present"
        )

        # Generate signature ID
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        signature_id = f"dna_{intent_id}_{timestamp_str}"

        # Build signature
        # CRITICAL RED TEAM FIX: Use derivation.derive_id
        signature = StyleSignature(
            signature_id=signature_id,
            intent_id=intent_id,
            derive_id=derivation.derive_id,  # RED TEAM FIX
            metrics=metrics,
            notes=f"DNA snapshot for intent {intent_id}"
        )

        # Compute embedding from metrics
        signature.embedding = aggregate_metric_vector(signature)

        logger.info(f"Encoded DNA signature: {signature_id}")
        logger.debug(f"  Metrics: {len(metrics)}, Embedding dim: {len(signature.embedding)}")

        return signature
