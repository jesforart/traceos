"""
Integration tests for Dual DNA Engine (Cognitive Kernel v2.5 Session 2)

Tests all functionality:
- Placeholder vector computation (128-dim validated)
- Full ingestion pipeline
- Composite key retrieval
- Proper delegation pattern
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from tracememory.models.memory import STYLE_VECTOR_DIM
from tracememory.storage.memory_storage import MemoryStorage
from tracememory.storage.telemetry_store import TelemetryStore
from tracememory.dual_dna.engine import DualDNAEngine


@pytest.fixture
def temp_db():
    """Use temp directory for test database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_dual_dna.db"


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


def test_stroke_dna_computation_validates_128_dim(engine):
    """
    RED TEAM FIX #4: Test that stroke DNA is exactly 128-dim
    """
    strokes = [
        {"x": i * 10.0, "y": i * 20.0, "p": 0.5 + i * 0.01, "t": i * 100.0, "tilt": 0.1}
        for i in range(50)
    ]

    stroke_dna = engine._compute_stroke_dna(strokes)

    assert len(stroke_dna) == STYLE_VECTOR_DIM
    assert all(isinstance(v, float) for v in stroke_dna)


def test_image_dna_computation_validates_128_dim(engine):
    """
    RED TEAM FIX #4: Test that image DNA is exactly 128-dim
    """
    # Create synthetic image (100x100 RGB)
    image = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)

    image_dna = engine._compute_image_dna(image)

    assert len(image_dna) == STYLE_VECTOR_DIM
    assert all(isinstance(v, float) for v in image_dna)


def test_temporal_dna_computation_validates_128_dim(engine):
    """
    RED TEAM FIX #4: Test that temporal DNA is exactly 128-dim
    """
    strokes = [
        {"x": 0, "y": 0, "p": 0.5, "t": i * 50.0, "tilt": 0}
        for i in range(100)
    ]

    temporal_dna = engine._compute_temporal_dna(strokes)

    assert len(temporal_dna) == STYLE_VECTOR_DIM
    assert all(isinstance(v, float) for v in temporal_dna)


def test_empty_strokes_returns_zero_vector(engine):
    """Test that empty stroke list returns valid zero vector"""
    stroke_dna = engine._compute_stroke_dna([])

    assert len(stroke_dna) == STYLE_VECTOR_DIM
    assert all(v == 0.0 for v in stroke_dna)


def test_empty_image_returns_zero_vector(engine):
    """Test that empty image returns valid zero vector"""
    empty_image = np.array([])

    image_dna = engine._compute_image_dna(empty_image)

    assert len(image_dna) == STYLE_VECTOR_DIM
    assert all(v == 0.0 for v in image_dna)


def test_full_ingestion_pipeline(engine):
    """
    Test full ingestion pipeline with all components.

    RED TEAM FIX #3: Uses composite key (session_id, artifact_id)
    RED TEAM FIX #4: All vectors validated to 128-dim
    """
    session_id = "test_session"
    artifact_id = "artifact_001"

    strokes = [
        {"x": i * 5.0, "y": i * 10.0, "p": 0.6, "t": i * 80.0, "tilt": 0.2}
        for i in range(30)
    ]

    image = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)

    intent = {
        "emotional_register": {"joy": 0.9, "playful": 0.7},
        "target_audience": "kidlit",
        "style_keywords": ["organic", "whimsical"],
        "source": "user_prompt"
    }

    tags = ["test", "dual_dna", "full_pipeline"]
    notes = "Full integration test"

    # Ingest artifact
    memory_block_id, style_dna_id, intent_profile_id = engine.ingest_artifact(
        session_id=session_id,
        artifact_id=artifact_id,
        image_data=image,
        strokes=strokes,
        intent=intent,
        tags=tags,
        notes=notes
    )

    # Validate all IDs returned
    assert memory_block_id is not None
    assert style_dna_id is not None
    assert intent_profile_id is not None

    # Retrieve and validate CognitiveMemoryBlock
    memory_block = engine.storage.get_cognitive_memory_block(memory_block_id)
    assert memory_block.session_id == session_id
    assert memory_block.artifact_id == artifact_id
    assert memory_block.tags == tags
    assert memory_block.notes == notes

    # Retrieve and validate StyleDNA
    style_dna = engine.storage.get_style_dna(style_dna_id)
    assert style_dna.artifact_id == artifact_id
    assert len(style_dna.stroke_dna) == STYLE_VECTOR_DIM
    assert len(style_dna.image_dna) == STYLE_VECTOR_DIM
    assert len(style_dna.temporal_dna) == STYLE_VECTOR_DIM

    # Retrieve and validate IntentProfile
    intent_profile = engine.storage.get_intent_profile(intent_profile_id)
    assert intent_profile.session_id == session_id
    assert intent_profile.artifact_id == artifact_id
    assert intent_profile.emotional_register["joy"] == 0.9
    assert "organic" in intent_profile.style_keywords


def test_ingestion_without_optional_fields(engine):
    """Test ingestion pipeline with minimal required fields"""
    session_id = "minimal_session"
    artifact_id = "minimal_artifact"

    # Only strokes, no image or intent
    strokes = [
        {"x": i * 2.0, "y": i * 3.0, "p": 0.5, "t": i * 50.0, "tilt": 0}
        for i in range(10)
    ]

    memory_block_id, style_dna_id, intent_profile_id = engine.ingest_artifact(
        session_id=session_id,
        artifact_id=artifact_id,
        strokes=strokes
    )

    # Memory block and style DNA should exist
    assert memory_block_id is not None
    assert style_dna_id is not None

    # Intent should be None (not provided)
    assert intent_profile_id is None

    # Validate StyleDNA has only stroke and temporal DNA
    style_dna = engine.storage.get_style_dna(style_dna_id)
    assert style_dna.stroke_dna is not None
    assert style_dna.temporal_dna is not None
    assert style_dna.image_dna is None  # Not provided


def test_composite_key_retrieval(engine):
    """
    RED TEAM FIX #3: Test retrieval using composite key (session_id, artifact_id)
    """
    session_id = "session_composite"
    artifact_id = "artifact_composite"

    strokes = [{"x": 1, "y": 2, "p": 0.5, "t": 100, "tilt": 0}]

    # Ingest artifact
    engine.ingest_artifact(
        session_id=session_id,
        artifact_id=artifact_id,
        strokes=strokes
    )

    # Retrieve using composite key
    dual_profile = engine.get_dual_profile(session_id, artifact_id)

    assert dual_profile is not None
    assert dual_profile["memory_block"] is not None
    assert dual_profile["style_dna"] is not None
    assert dual_profile["memory_block"].session_id == session_id
    assert dual_profile["memory_block"].artifact_id == artifact_id


def test_get_dual_profile_returns_none_for_nonexistent(engine):
    """Test that get_dual_profile returns None for non-existent artifact"""
    dual_profile = engine.get_dual_profile("nonexistent_session", "nonexistent_artifact")

    assert dual_profile is None


def test_same_artifact_id_different_sessions(engine):
    """
    RED TEAM FIX #3: Test that same artifact_id can exist in different sessions
    """
    artifact_id = "shared_artifact_id"

    strokes1 = [{"x": 10, "y": 20, "p": 0.5, "t": 100, "tilt": 0}]
    strokes2 = [{"x": 30, "y": 40, "p": 0.6, "t": 200, "tilt": 0.1}]

    # Ingest same artifact_id in two different sessions
    mb_id_1, _, _ = engine.ingest_artifact(
        session_id="session_A",
        artifact_id=artifact_id,
        strokes=strokes1
    )

    mb_id_2, _, _ = engine.ingest_artifact(
        session_id="session_B",
        artifact_id=artifact_id,
        strokes=strokes2
    )

    # Both should succeed with different memory block IDs
    assert mb_id_1 != mb_id_2

    # Retrieve each using composite key
    profile_1 = engine.get_dual_profile("session_A", artifact_id)
    profile_2 = engine.get_dual_profile("session_B", artifact_id)

    assert profile_1["memory_block"].session_id == "session_A"
    assert profile_2["memory_block"].session_id == "session_B"
    assert profile_1["memory_block"].id != profile_2["memory_block"].id


def test_telemetry_chunk_saved(engine):
    """
    RED TEAM FIX #2: Test that telemetry chunk is saved and retrievable
    """
    session_id = "telemetry_session"
    artifact_id = "telemetry_artifact"

    strokes = [
        {"x": i * 1.0, "y": i * 2.0, "p": 0.5, "t": i * 10.0, "tilt": 0}
        for i in range(20)
    ]

    # Ingest with telemetry
    engine.ingest_artifact(
        session_id=session_id,
        artifact_id=artifact_id,
        strokes=strokes
    )

    # Retrieve telemetry chunks
    chunks = engine.storage.get_telemetry_chunks_by_session(session_id)

    assert len(chunks) == 1
    assert chunks[0].session_id == session_id
    assert chunks[0].artifact_id == artifact_id
    assert chunks[0].chunk_row_count == 20


def test_vector_computation_numerical_stability(engine):
    """Test that vector computation is numerically stable"""
    # Create strokes with extreme values
    strokes_extreme = [
        {"x": 1e6, "y": 1e6, "p": 1.0, "t": 1e9, "tilt": 0.9},
        {"x": -1e6, "y": -1e6, "p": 0.0, "t": 0.0, "tilt": 0.0}
    ]

    stroke_dna = engine._compute_stroke_dna(strokes_extreme)

    # Should not contain NaN or Inf
    assert len(stroke_dna) == STYLE_VECTOR_DIM
    assert all(np.isfinite(v) for v in stroke_dna)


def test_engine_without_telemetry_store(storage):
    """Test that engine works without TelemetryStore (optional dependency)"""
    engine_no_telemetry = DualDNAEngine(memory_storage=storage, telemetry_store=None)

    strokes = [{"x": 1, "y": 2, "p": 0.5, "t": 100, "tilt": 0}]

    # Should still work, but telemetry won't be saved
    mb_id, style_id, _ = engine_no_telemetry.ingest_artifact(
        session_id="no_tel_session",
        artifact_id="no_tel_artifact",
        strokes=strokes
    )

    assert mb_id is not None
    assert style_id is not None


def test_grayscale_image_dna_computation(engine):
    """Test image DNA computation with grayscale image"""
    # Grayscale image (H, W)
    gray_image = np.random.randint(0, 256, size=(64, 64), dtype=np.uint8)

    image_dna = engine._compute_image_dna(gray_image)

    assert len(image_dna) == STYLE_VECTOR_DIM
    assert all(np.isfinite(v) for v in image_dna)


if __name__ == "__main__":
    print("=" * 70)
    print("Cognitive Kernel v2.5 - Session 2: Dual DNA Engine Tests")
    print("=" * 70)
    print()
    print("To run tests:")
    print("  pytest tests/test_dual_dna_engine.py -v")
    print()
    print("Tests cover:")
    print("  - Placeholder vector computation (128-dim validated)")
    print("  - Full ingestion pipeline")
    print("  - Composite key retrieval")
    print("  - RED TEAM fixes #2, #3, #4")
    print()
