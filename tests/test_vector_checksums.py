"""
Vector Checksum Tests (v2.6 Hardening - Task 4)

Tests automatic checksum generation and verification for StyleDNA vectors.

HARDENING v2.6 - Task 4: Detects vector corruption through checksums.
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from tracememory.storage.memory_storage import MemoryStorage
from tracememory.storage.telemetry_store import TelemetryStore
from tracememory.dual_dna.engine import DualDNAEngine
from tracememory.models.memory import STYLE_VECTOR_DIM
from tracememory.storage.vector_utils import (
    compute_vector_checksum,
    verify_vector_checksum,
    compute_style_dna_checksum,
    verify_style_dna_checksum,
    compute_l2_norm
)


@pytest.fixture
def temp_db():
    """Use temp directory for test database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
def storage(temp_db):
    """Create MemoryStorage with Cognitive Kernel migration"""
    storage = MemoryStorage(str(temp_db))
    storage.run_cognitive_kernel_migration()
    return storage


@pytest.fixture
def telemetry_store():
    """Create TelemetryStore in temp directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield TelemetryStore(base_path=tmpdir)


@pytest.fixture
def engine(storage, telemetry_store):
    """Create DualDNAEngine with injected dependencies"""
    return DualDNAEngine(
        memory_storage=storage,
        telemetry_store=telemetry_store
    )


def test_compute_vector_checksum():
    """Test that vector checksum is deterministic"""
    vec = [1.0, 2.0, 3.0, 4.0, 5.0]

    checksum1 = compute_vector_checksum(vec)
    checksum2 = compute_vector_checksum(vec)

    # Should be deterministic
    assert checksum1 == checksum2

    # Should be SHA-256 (64 hex characters)
    assert len(checksum1) == 64
    assert all(c in '0123456789abcdef' for c in checksum1)


def test_verify_vector_checksum_valid():
    """Test checksum verification with valid vector"""
    vec = [10.0, 20.0, 30.0, 40.0]

    checksum = compute_vector_checksum(vec)

    # Same vector should verify
    assert verify_vector_checksum(vec, checksum) is True


def test_verify_vector_checksum_corrupted():
    """Test checksum verification detects corruption"""
    vec = [10.0, 20.0, 30.0, 40.0]
    checksum = compute_vector_checksum(vec)

    # Corrupt the vector
    corrupted_vec = [10.0, 20.0, 30.1, 40.0]  # Changed one value

    # Should detect corruption
    assert verify_vector_checksum(corrupted_vec, checksum) is False


def test_compute_style_dna_checksum():
    """Test combined StyleDNA checksum computation"""
    stroke_dna = [1.0] * STYLE_VECTOR_DIM
    image_dna = [2.0] * STYLE_VECTOR_DIM
    temporal_dna = [3.0] * STYLE_VECTOR_DIM

    checksum = compute_style_dna_checksum(stroke_dna, image_dna, temporal_dna)

    assert checksum is not None
    assert len(checksum) == 64


def test_compute_style_dna_checksum_partial():
    """Test StyleDNA checksum with only some vectors present"""
    stroke_dna = [1.0] * STYLE_VECTOR_DIM

    # Only stroke DNA, no image or temporal
    checksum = compute_style_dna_checksum(stroke_dna, None, None)

    assert checksum is not None
    assert len(checksum) == 64


def test_compute_style_dna_checksum_empty():
    """Test StyleDNA checksum with no vectors"""
    checksum = compute_style_dna_checksum(None, None, None)

    # Should return None if no vectors
    assert checksum is None


def test_verify_style_dna_checksum_valid():
    """Test StyleDNA checksum verification"""
    stroke_dna = [1.0] * STYLE_VECTOR_DIM
    image_dna = [2.0] * STYLE_VECTOR_DIM
    temporal_dna = [3.0] * STYLE_VECTOR_DIM

    checksum = compute_style_dna_checksum(stroke_dna, image_dna, temporal_dna)

    # Should verify with same vectors
    assert verify_style_dna_checksum(stroke_dna, image_dna, temporal_dna, checksum) is True


def test_verify_style_dna_checksum_corrupted():
    """Test that StyleDNA checksum detects corruption"""
    stroke_dna = [1.0] * STYLE_VECTOR_DIM
    image_dna = [2.0] * STYLE_VECTOR_DIM
    temporal_dna = [3.0] * STYLE_VECTOR_DIM

    checksum = compute_style_dna_checksum(stroke_dna, image_dna, temporal_dna)

    # Corrupt one vector
    corrupted_stroke = [1.1] * STYLE_VECTOR_DIM

    # Should detect corruption
    assert verify_style_dna_checksum(corrupted_stroke, image_dna, temporal_dna, checksum) is False


def test_auto_checksum_generation_on_ingest(engine):
    """
    HARDENING v2.6 - Task 4: Test that checksums are auto-generated
    """
    strokes = [
        {"x": i, "y": i * 2, "p": 0.5, "t": i * 100.0, "tilt": 0.0}
        for i in range(20)
    ]

    # Ingest artifact
    memory_block_id, style_dna_id, _ = engine.ingest_artifact(
        session_id="checksum_session",
        artifact_id="checksum_artifact",
        strokes=strokes
    )

    # Retrieve StyleDNA
    style = engine.storage.get_style_dna(style_dna_id)

    # Checksum should be auto-generated
    assert style.checksum is not None
    assert len(style.checksum) == 64

    # L2 norm should also be computed
    assert style.l2_norm is not None
    assert style.l2_norm > 0.0


def test_checksum_verification_on_load(engine):
    """
    HARDENING v2.6 - Task 4: Test that checksums are verified on load
    """
    strokes = [
        {"x": i, "y": i, "p": 0.5, "t": i * 100.0, "tilt": 0.0}
        for i in range(10)
    ]

    # Ingest artifact with checksum
    _, style_dna_id, _ = engine.ingest_artifact(
        session_id="verify_session",
        artifact_id="verify_artifact",
        strokes=strokes
    )

    # Load should succeed (valid checksum)
    style = engine.storage.get_style_dna(style_dna_id)
    assert style is not None
    assert style.checksum is not None


def test_checksum_detects_corruption(engine):
    """
    HARDENING v2.6 - Task 4: Test that corrupted vectors are detected
    """
    strokes = [
        {"x": i, "y": i, "p": 0.5, "t": i * 100.0, "tilt": 0.0}
        for i in range(10)
    ]

    # Ingest artifact
    _, style_dna_id, _ = engine.ingest_artifact(
        session_id="corrupt_session",
        artifact_id="corrupt_artifact",
        strokes=strokes
    )

    # Manually corrupt the vector in database
    from tracememory.storage.migrations.v2_5_cognitive_kernel import vector_to_blob

    # Create a different vector (corruption)
    corrupted_vec = [99.0] * STYLE_VECTOR_DIM
    corrupted_blob = vector_to_blob(corrupted_vec)

    conn = engine.storage.get_connection()
    conn.execute(
        "UPDATE style_dna SET stroke_dna = ? WHERE id = ?",
        (corrupted_blob, style_dna_id)
    )
    conn.commit()
    conn.close()

    # Loading should detect corruption
    with pytest.raises(ValueError, match="checksum mismatch"):
        engine.storage.get_style_dna(style_dna_id)


def test_l2_norm_computation():
    """Test L2 norm (Euclidean length) computation"""
    # Simple case: [3, 4] -> norm should be 5
    vec = [3.0, 4.0]
    norm = compute_l2_norm(vec)
    assert abs(norm - 5.0) < 1e-6

    # Zero vector
    zero_vec = [0.0, 0.0, 0.0]
    assert compute_l2_norm(zero_vec) == 0.0

    # Unit vector
    unit_vec = [1.0, 0.0, 0.0]
    assert abs(compute_l2_norm(unit_vec) - 1.0) < 1e-6


def test_l2_norm_auto_generated(engine):
    """Test that L2 norm is auto-generated for StyleDNA"""
    strokes = [
        {"x": i, "y": i, "p": 0.5, "t": i * 100.0, "tilt": 0.0}
        for i in range(10)
    ]

    _, style_dna_id, _ = engine.ingest_artifact(
        session_id="l2_session",
        artifact_id="l2_artifact",
        strokes=strokes
    )

    style = engine.storage.get_style_dna(style_dna_id)

    # L2 norm should be present
    assert style.l2_norm is not None
    assert style.l2_norm > 0.0

    # Verify it matches computed norm
    if style.stroke_dna:
        expected_norm = compute_l2_norm(style.stroke_dna)
        assert abs(style.l2_norm - expected_norm) < 1e-6


def test_checksum_with_partial_vectors(engine):
    """Test checksum generation with only some vectors present"""
    # Only provide image data, no strokes
    image = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)

    _, style_dna_id, _ = engine.ingest_artifact(
        session_id="partial_session",
        artifact_id="partial_artifact",
        image_data=image
    )

    style = engine.storage.get_style_dna(style_dna_id)

    # Checksum should be present (computed from image_dna only)
    assert style.checksum is not None

    # Only image_dna should be present
    assert style.image_dna is not None
    assert style.stroke_dna is None
    assert style.temporal_dna is None


def test_empty_vector_checksum():
    """Test checksum computation for empty vector"""
    empty_vec = []
    checksum = compute_vector_checksum(empty_vec)

    # Should return hash of empty bytes
    assert checksum is not None
    assert len(checksum) == 64


def test_checksum_idempotent_across_ingest(engine):
    """Test that same data produces same checksum"""
    strokes = [{"x": 1.0, "y": 2.0, "p": 0.5, "t": 100.0, "tilt": 0.0}] * 5

    # Ingest twice
    _, style_id_1, _ = engine.ingest_artifact(
        "session1", "artifact1", strokes=strokes
    )

    _, style_id_2, _ = engine.ingest_artifact(
        "session2", "artifact2", strokes=strokes
    )

    style1 = engine.storage.get_style_dna(style_id_1)
    style2 = engine.storage.get_style_dna(style_id_2)

    # Same input data should produce same checksum
    # (assuming deterministic vector computation)
    assert style1.checksum == style2.checksum


if __name__ == "__main__":
    print("=" * 70)
    print("Cognitive Kernel v2.6 - Task 4: Vector Checksum Tests")
    print("=" * 70)
    print()
    print("To run tests:")
    print("  pytest tests/test_vector_checksums.py -v")
    print()
    print("Tests cover:")
    print("  - Automatic checksum generation on save")
    print("  - Automatic verification on load")
    print("  - Corruption detection")
    print("  - L2 norm computation")
    print("  - Partial vector checksums")
    print()
    print("HARDENING: Prevents silent vector corruption in storage.")
    print()
