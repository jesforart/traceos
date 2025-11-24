"""
Vector Checksum Utilities for Cognitive Kernel v2.6

HARDENING v2.6 - Task 4: Automatic Vector Checksum Generation

Problem: StyleDNA.checksum field exists but is not automatically generated
or validated, missing potential vector corruption.

Solution: Automatic checksum generation on save, verification on load.
"""

import hashlib
import struct
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def compute_vector_checksum(vector: List[float]) -> str:
    """
    Compute SHA-256 checksum of a vector.

    HARDENING v2.6 - Task 4: Detects corruption in stored vectors.

    The checksum is computed from the binary representation (float32)
    to match the BLOB storage format.

    Args:
        vector: List of floats (any dimension)

    Returns:
        SHA-256 hex digest (64 characters)
    """
    if not vector:
        return hashlib.sha256(b'').hexdigest()

    # Convert to bytes (same format as vector_to_blob)
    blob = struct.pack(f'{len(vector)}f', *vector)

    return hashlib.sha256(blob).hexdigest()


def verify_vector_checksum(vector: List[float], expected_checksum: str) -> bool:
    """
    Verify that a vector matches its checksum.

    HARDENING v2.6 - Task 4: Validates vector integrity.

    Args:
        vector: List of floats to verify
        expected_checksum: Expected SHA-256 hex digest

    Returns:
        True if valid, False if corrupted
    """
    actual = compute_vector_checksum(vector)
    return actual == expected_checksum


def compute_style_dna_checksum(
    stroke_dna: Optional[List[float]],
    image_dna: Optional[List[float]],
    temporal_dna: Optional[List[float]]
) -> Optional[str]:
    """
    Compute combined checksum for StyleDNA.

    HARDENING v2.6 - Task 4: Combines all three DNA vectors into single checksum.

    Args:
        stroke_dna: Optional stroke DNA vector
        image_dna: Optional image DNA vector
        temporal_dna: Optional temporal DNA vector

    Returns:
        SHA-256 hex digest if any vector present, None otherwise
    """
    # Combine all non-None vectors
    combined = []

    if stroke_dna:
        combined.extend(stroke_dna)
    if image_dna:
        combined.extend(image_dna)
    if temporal_dna:
        combined.extend(temporal_dna)

    if not combined:
        return None

    return compute_vector_checksum(combined)


def verify_style_dna_checksum(
    stroke_dna: Optional[List[float]],
    image_dna: Optional[List[float]],
    temporal_dna: Optional[List[float]],
    expected_checksum: Optional[str]
) -> bool:
    """
    Verify StyleDNA checksum against combined vectors.

    HARDENING v2.6 - Task 4: Validates all three DNA vectors at once.

    Args:
        stroke_dna: Optional stroke DNA vector
        image_dna: Optional image DNA vector
        temporal_dna: Optional temporal DNA vector
        expected_checksum: Expected SHA-256 hex digest

    Returns:
        True if valid or no checksum provided, False if corrupted
    """
    if expected_checksum is None:
        # No checksum to verify
        logger.debug("No checksum provided for verification")
        return True

    actual = compute_style_dna_checksum(stroke_dna, image_dna, temporal_dna)

    if actual != expected_checksum:
        logger.error(
            f"StyleDNA checksum mismatch! "
            f"Expected: {expected_checksum}, Actual: {actual}"
        )
        return False

    return True


def compute_l2_norm(vector: List[float]) -> float:
    """
    Compute L2 norm (Euclidean length) of a vector.

    Useful for:
    - Vector similarity searches
    - Normalization
    - Magnitude comparison

    Args:
        vector: List of floats

    Returns:
        L2 norm (non-negative float)
    """
    if not vector:
        return 0.0

    sum_of_squares = sum(x * x for x in vector)
    return sum_of_squares ** 0.5
