"""
ULID (Universally Unique Lexicographically Sortable Identifier) generation.

ULIDs are:
- 128-bit compatible with UUID
- Lexicographically sortable
- Timestamp-based (48 bits for millisecond precision)
- Random component (80 bits)

Format: 01HBKZ5Y8Q9X2N4V7M1R3P6W0S (26 characters, Crockford's Base32)
"""

import time
import random
import string

# Crockford's Base32 alphabet (excludes I, L, O, U to avoid confusion)
BASE32_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def generate_ulid() -> str:
    """
    Generate a ULID string.

    Returns:
        26-character ULID string
        Example: 01HBKZ5Y8Q9X2N4V7M1R3P6W0S
    """
    # Get timestamp in milliseconds (48 bits)
    timestamp_ms = int(time.time() * 1000)

    # Encode timestamp (10 characters)
    timestamp_part = _encode_timestamp(timestamp_ms, 10)

    # Generate random component (16 characters, 80 bits)
    random_part = _encode_random(16)

    return timestamp_part + random_part


def _encode_timestamp(timestamp_ms: int, length: int) -> str:
    """
    Encode timestamp as Base32 string.

    Args:
        timestamp_ms: Unix timestamp in milliseconds
        length: Desired string length (typically 10)

    Returns:
        Base32 encoded timestamp
    """
    result = []
    for _ in range(length):
        result.append(BASE32_ALPHABET[timestamp_ms % 32])
        timestamp_ms //= 32

    return ''.join(reversed(result))


def _encode_random(length: int) -> str:
    """
    Generate random Base32 string.

    Args:
        length: Desired string length (typically 16)

    Returns:
        Random Base32 string
    """
    return ''.join(random.choice(BASE32_ALPHABET) for _ in range(length))


def ulid_to_timestamp(ulid: str) -> int:
    """
    Extract timestamp from ULID.

    Args:
        ulid: ULID string

    Returns:
        Unix timestamp in milliseconds
    """
    timestamp_part = ulid[:10]
    timestamp_ms = 0

    for char in timestamp_part:
        timestamp_ms = timestamp_ms * 32 + BASE32_ALPHABET.index(char)

    return timestamp_ms
