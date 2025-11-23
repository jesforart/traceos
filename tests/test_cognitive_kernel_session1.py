"""
Integration tests for Cognitive Kernel v2.5 Session 1: Storage Foundation

Tests all RED TEAM fixes:
- FIX #1: Migration idempotence
- FIX #2: Parquet row-group writer (requires pyarrow)
- FIX #3: Composite uniqueness for artifact_id
- FIX #4: Vector dimension validation
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from tracememory.models.memory import (
    CognitiveMemoryBlock, StyleDNA, IntentProfile, TelemetryChunk,
    STYLE_VECTOR_DIM, generate_id
)
from tracememory.storage.memory_storage import MemoryStorage


@pytest.fixture
def temp_db():
    """Use temp directory for test database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_cognitive.db"


@pytest.fixture
def storage(temp_db):
    """Create MemoryStorage with Cognitive Kernel migration"""
    storage = MemoryStorage(str(temp_db))
    storage.run_cognitive_kernel_migration()
    return storage


def test_cognitive_memory_block_roundtrip(storage):
    """Test creating and retrieving a CognitiveMemoryBlock"""
    block = CognitiveMemoryBlock(
        session_id="test_session",
        artifact_id="test_artifact",
        tags=["test", "cognitive"],
        notes="Test memory block"
    )

    block_id = storage.save_cognitive_memory_block(block)
    retrieved = storage.get_cognitive_memory_block(block_id)

    assert retrieved is not None
    assert retrieved.session_id == "test_session"
    assert retrieved.tags == ["test", "cognitive"]


def test_style_dna_vector_validation(storage):
    """
    RED TEAM FIX #4: Test that invalid vector dimensions are rejected
    """
    # Valid 128-dim vectors
    valid_vec = np.random.rand(STYLE_VECTOR_DIM).tolist()

    style = StyleDNA(
        artifact_id="test_art",
        stroke_dna=valid_vec
    )

    style_id = storage.save_style_dna(style)
    assert style_id is not None

    # Invalid dimensions should raise ValueError
    with pytest.raises(ValueError, match="must be exactly 128 dimensions"):
        bad_style = StyleDNA(
            artifact_id="test_art",
            stroke_dna=[1.0, 2.0, 3.0]  # Only 3 dims - WRONG!
        )


def test_style_dna_vector_storage_roundtrip(storage):
    """Test storing and retrieving StyleDNA with validated vectors"""
    # Create validated 128-dim vectors
    stroke_vec = np.random.rand(STYLE_VECTOR_DIM).tolist()
    image_vec = np.random.rand(STYLE_VECTOR_DIM).tolist()
    temporal_vec = np.random.rand(STYLE_VECTOR_DIM).tolist()

    style = StyleDNA(
        artifact_id="test_art",
        stroke_dna=stroke_vec,
        image_dna=image_vec,
        temporal_dna=temporal_vec
    )

    style_id = storage.save_style_dna(style)
    retrieved = storage.get_style_dna(style_id)

    assert retrieved is not None
    assert len(retrieved.stroke_dna) == STYLE_VECTOR_DIM
    assert np.allclose(retrieved.stroke_dna, stroke_vec, atol=1e-6)


def test_artifact_id_uniqueness_per_session(storage):
    """
    RED TEAM FIX #3: Test that artifact_id is unique per session
    """
    # Same artifact_id in different sessions - should work
    block1 = CognitiveMemoryBlock(
        session_id="session_1",
        artifact_id="artifact_A"
    )
    block2 = CognitiveMemoryBlock(
        session_id="session_2",
        artifact_id="artifact_A"  # Same artifact_id, different session
    )

    storage.save_cognitive_memory_block(block1)
    storage.save_cognitive_memory_block(block2)

    # Retrieve by composite key
    retrieved1 = storage.get_cognitive_memory_block_by_artifact("session_1", "artifact_A")
    retrieved2 = storage.get_cognitive_memory_block_by_artifact("session_2", "artifact_A")

    assert retrieved1.session_id == "session_1"
    assert retrieved2.session_id == "session_2"
    assert retrieved1.id != retrieved2.id  # Different blocks


def test_migration_idempotence(temp_db):
    """
    RED TEAM FIX #1: Test that running migration twice is safe
    """
    storage1 = MemoryStorage(str(temp_db))
    storage1.run_cognitive_kernel_migration()

    # Save some data
    block = CognitiveMemoryBlock(session_id="test", artifact_id="test")
    storage1.save_cognitive_memory_block(block)

    # "Restart" and re-run migration
    storage2 = MemoryStorage(str(temp_db))
    storage2.run_cognitive_kernel_migration()  # Should be safe

    # Data should still be there
    retrieved = storage2.get_cognitive_memory_block(block.id)
    assert retrieved is not None
    assert retrieved.session_id == "test"


def test_intent_profile_roundtrip(storage):
    """Test creating and retrieving an IntentProfile"""
    intent = IntentProfile(
        session_id="test_session",
        artifact_id="test_artifact",
        emotional_register={"joy": 0.8, "chaos": 0.3},
        target_audience="kidlit",
        style_keywords=["organic", "playful"],
        source="user_prompt"
    )

    intent_id = storage.save_intent_profile(intent)
    retrieved = storage.get_intent_profile(intent_id)

    assert retrieved is not None
    assert retrieved.emotional_register["joy"] == 0.8
    assert "organic" in retrieved.style_keywords


def test_telemetry_chunk_metadata(storage):
    """Test saving and retrieving TelemetryChunk metadata"""
    chunk = TelemetryChunk(
        session_id="test_session",
        artifact_id="test_artifact",
        parquet_path="data/telemetry/session_test.parquet",
        chunk_row_count=100,
        total_session_rows=100
    )

    chunk_id = storage.save_telemetry_chunk(chunk)
    retrieved = storage.get_telemetry_chunk(chunk_id)

    assert retrieved is not None
    assert retrieved.chunk_row_count == 100
    assert retrieved.total_session_rows == 100


# Parquet tests require pyarrow - skip if not available
try:
    import pyarrow
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False


@pytest.mark.skipif(not PYARROW_AVAILABLE, reason="PyArrow not installed")
def test_telemetry_row_group_writer():
    """
    RED TEAM FIX #2: Test scalable Parquet row-group writer
    """
    from tracememory.storage.telemetry_store import TelemetryStore

    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry = TelemetryStore(base_path=tmpdir)

        session_id = "test_session"

        # Write first batch
        strokes1 = [
            {"x": i, "y": i*2, "p": 0.5, "t": i*100.0, "tilt": 0.1}
            for i in range(10)
        ]
        chunk1 = telemetry.save_strokes(session_id, "art1", strokes1)

        assert chunk1.chunk_row_count == 10
        assert chunk1.total_session_rows == 10

        # Write second batch (append via row group)
        strokes2 = [
            {"x": i, "y": i*3, "p": 0.6, "t": i*100.0, "tilt": 0.2}
            for i in range(15)
        ]
        chunk2 = telemetry.save_strokes(session_id, "art2", strokes2)

        assert chunk2.chunk_row_count == 15
        assert chunk2.total_session_rows == 25  # 10 + 15

        # Close session to flush
        telemetry.close_session(session_id)

        # Load entire session
        all_strokes = telemetry.load_session_strokes(session_id)
        assert len(all_strokes) == 25


if __name__ == "__main__":
    print("=" * 70)
    print("Cognitive Kernel v2.5 - Session 1 Integration Tests")
    print("=" * 70)
    print()
    print("To run tests:")
    print("  pytest tests/test_cognitive_kernel_session1.py -v")
    print()
    print("Note: Install pyarrow for full test coverage:")
    print("  pip install pyarrow")
    print()
