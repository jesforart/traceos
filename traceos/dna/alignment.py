"""
DNA Alignment Utilities

Pure-python utilities for computing alignment scores between
StyleSignatures based on their embeddings and metrics.

Uses cosine similarity to measure identity coherence over time.

@provenance traceos_dna_v1
@organ identity
"""

import math
from typing import List

from .schemas import StyleSignature


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Compute cosine similarity between two vectors (0-1).

    Returns 1.0 for identical vectors, 0.0 for orthogonal.
    """
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def aggregate_metric_vector(signature: StyleSignature) -> List[float]:
    """
    Produce a deterministic numeric embedding from metrics.

    Sort metrics by name to create stable ordering, then
    multiply value * weight for each metric.

    This creates a consistent vector representation for alignment.
    """
    items = sorted(signature.metrics.items(), key=lambda kv: kv[0])
    return [m.value * m.weight for _, m in items]


def alignment_score(
    base: StyleSignature,
    candidate: StyleSignature
) -> float:
    """
    Compute identity alignment between two signatures (0-1).

    Uses cosine similarity over aggregated metric vectors.
    High scores indicate strong style consistency.
    """
    base_vec = aggregate_metric_vector(base)
    cand_vec = aggregate_metric_vector(candidate)
    return cosine_similarity(base_vec, cand_vec)
