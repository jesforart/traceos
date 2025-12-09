"""
Codify Handler - Captures learnings into design DNA.

UPDATED FOR PHASE 4:
- Writes StyleSignatures to DNA store
- Updates lineage with alignment tracking
- Integrates with Creative DNA Engine

RED TEAM FIX: DNAStore must be passed in constructor.
CIRCULAR IMPORT FIX: DNA imports moved to method level.

@provenance traceos_protocol_v1
@organ kernel
"""

import logging
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from .schemas import CodifyOutput, EvaluateOutput, DeriveOutput
from .persistence import ProtocolStorage

if TYPE_CHECKING:
    from traceos.dna.store import DNAStore

logger = logging.getLogger(__name__)


class CodifyHandler:
    """
    Captures implementation learnings into TraceOS design DNA.

    Phase 4: Also captures Creative DNA signatures and lineage.
    """

    def __init__(self, storage: ProtocolStorage, dna_store: "DNAStore"):
        """
        Initialize CodifyHandler.

        Args:
            storage: Protocol storage for codifications
            dna_store: DNA store for style signatures (RED TEAM FIX: required)
        """
        self.storage = storage
        self.dna_store = dna_store
        logger.debug("CodifyHandler initialized with DNA store")

    def codify(
        self,
        derivation: DeriveOutput,
        evaluate_output: EvaluateOutput
    ) -> CodifyOutput:
        """
        Extract patterns/lessons and create DNA signature.

        Args:
            derivation: DeriveOutput for this intent
            evaluate_output: Output from evaluation step

        Returns:
            CodifyOutput with learnings and DNA reference
        """
        # Lazy imports to avoid circular dependency
        from traceos.dna.encoder import DNAEncoder
        from traceos.dna.alignment import alignment_score
        from traceos.dna.schemas import DNALineageNode

        logger.info(f"Codifying learnings for derive: {evaluate_output.derive_id}")

        patterns: List[str] = []
        lessons: List[str] = []

        # Extract patterns and lessons from Spark reviews
        for review in evaluate_output.reviews:
            for comment in review.comments:
                if "pattern" in comment.message.lower():
                    patterns.append(comment.message)
                else:
                    lessons.append(f"[{review.spark}] {comment.message}")

        # DNA ENCODING
        logger.debug("Creating DNA signature from evaluation...")
        signature = DNAEncoder.from_evaluation(
            intent_id=evaluate_output.intent_id,
            derivation=derivation,
            evaluation=evaluate_output
        )
        self.dna_store.save_signature(signature)

        # Update lineage
        lineage = self.dna_store.load_lineage()
        parent_id = lineage[-1].signature_id if lineage else None

        align_to_parent = None
        if parent_id:
            parent_sig = self.dna_store.load_signature(parent_id)
            if parent_sig:
                align_to_parent = alignment_score(parent_sig, signature)
                logger.debug(f"DNA alignment to parent: {align_to_parent:.3f}")

        node = DNALineageNode(
            signature_id=signature.signature_id,
            parent_signature_id=parent_id,
            intent_id=evaluate_output.intent_id,
            alignment_to_parent=align_to_parent
        )

        lineage.append(node)
        self.dna_store.save_lineage(lineage)

        # Build codified output
        output = CodifyOutput(
            intent_id=evaluate_output.intent_id,
            derive_id=evaluate_output.derive_id,
            codified={
                "patterns": patterns,
                "lessons": lessons,
                "timestamp": datetime.utcnow().isoformat(),
                "dna_signature_id": signature.signature_id,
                "dna_alignment_to_parent": align_to_parent
            }
        )

        # Persist codification
        self.storage.save_codification(output)

        logger.info(
            f"Captured {len(patterns)} patterns, {len(lessons)} lessons, "
            f"DNA signature={signature.signature_id}, alignment={align_to_parent}"
        )

        return output

    def get_codification(self, derive_id: str) -> Optional[CodifyOutput]:
        """Load existing codification by derive ID."""
        return self.storage.load_codification(derive_id)
