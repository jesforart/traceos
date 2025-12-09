"""
TraceOS Creative DNA Engine

Style memory and identity tracking for the organism.

The DNA Engine enables TraceOS to:
- Remember its creative identity over time
- Track style evolution through lineage
- Measure alignment between past and present work
- Provide Soul/Dream Sparks with identity context

CIRCULAR IMPORT FIX: DNAEncoder is NOT imported at module level.
Import it directly: from traceos.dna.encoder import DNAEncoder

@provenance traceos_dna_v1
@organ identity
"""

# Safe imports (no protocol dependencies)
from .schemas import (
    StyleMetric,
    StyleSignature,
    DNALineageNode,
    DNAProfileSummary
)
from .store import DNAStore
from .alignment import alignment_score, cosine_similarity, aggregate_metric_vector

# DNAEncoder NOT imported here to avoid circular import
# Import directly: from traceos.dna.encoder import DNAEncoder

__all__ = [
    # Schemas
    "StyleMetric",
    "StyleSignature",
    "DNALineageNode",
    "DNAProfileSummary",

    # Core classes
    "DNAStore",
    # "DNAEncoder" - import from traceos.dna.encoder directly

    # Utilities
    "alignment_score",
    "cosine_similarity",
    "aggregate_metric_vector"
]
