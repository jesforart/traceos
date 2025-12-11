"""
TraceOS Protocol Module

Defines the formal workflow for creative work:
    Intent -> Derive -> Evaluate -> Codify -> DNA

All protocol operations maintain full provenance.
"""

from traceos.protocol.schemas import (
    Intent,
    DeriveOutput,
    SparkReview,
    EvaluationResult,
    CodifyResult,
)

__all__ = [
    "Intent",
    "DeriveOutput",
    "SparkReview",
    "EvaluationResult",
    "CodifyResult",
]
