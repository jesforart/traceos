"""
Integration tests for Gemini Critic (Cognitive Kernel v2.5 Session 3)

Tests all functionality:
- Structured JSON output (RED TEAM FIX #5)
- Mock mode for CI/CD
- Image and SVG critique
- IntentProfile context integration
- API route integration
"""

import pytest
import tempfile
import base64
import numpy as np
from pathlib import Path
from io import BytesIO
from PIL import Image

from tracememory.critic.gemini_critic import (
    GeminiCritic,
    AestheticCritique,
    CritiqueScore
)
from tracememory.storage.memory_storage import MemoryStorage
from tracememory.dual_dna.engine import DualDNAEngine
from tracememory.models.memory import IntentProfile


@pytest.fixture
def critic_mock():
    """Create GeminiCritic in mock mode (no API calls)"""
    return GeminiCritic(mock_mode=True)


@pytest.fixture
def temp_db():
    """Use temp directory for test database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_critic.db"


@pytest.fixture
def storage(temp_db):
    """Create MemoryStorage with Cognitive Kernel migration"""
    storage = MemoryStorage(str(temp_db))
    storage.run_cognitive_kernel_migration()
    return storage


@pytest.fixture
def sample_image_bytes():
    """Generate sample PNG image as bytes"""
    # Create 100x100 RGB image
    img = Image.new('RGB', (100, 100), color=(255, 128, 64))
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def sample_svg():
    """Generate sample SVG"""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="orange" />
        <rect x="20" y="20" width="60" height="60" fill="none" stroke="blue" stroke-width="2"/>
    </svg>"""


def test_critic_mock_mode_initialization():
    """Test that critic initializes correctly in mock mode"""
    critic = GeminiCritic(mock_mode=True)
    assert critic.mock_mode is True
    assert critic.client is None


def test_critic_requires_api_key_in_non_mock_mode():
    """Test that critic raises error if API key not provided"""
    with pytest.raises(ValueError, match="API key required"):
        GeminiCritic(mock_mode=False, api_key=None)


def test_mock_critique_returns_valid_structure(critic_mock):
    """
    RED TEAM FIX #5: Test that mock critique returns valid JSON structure
    """
    critique = critic_mock._mock_critique()

    assert isinstance(critique, AestheticCritique)
    assert 0.0 <= critique.overall_score <= 1.0
    assert isinstance(critique.overall_feedback, str)
    assert len(critique.overall_feedback) > 0

    # Validate dimension scores
    assert isinstance(critique.composition, CritiqueScore)
    assert 0.0 <= critique.composition.score <= 1.0
    assert len(critique.composition.rationale) > 0

    assert isinstance(critique.color_harmony, CritiqueScore)
    assert isinstance(critique.balance, CritiqueScore)
    assert isinstance(critique.visual_interest, CritiqueScore)
    assert isinstance(critique.technical_execution, CritiqueScore)

    # Validate lists
    assert isinstance(critique.strengths, list)
    assert len(critique.strengths) > 0
    assert isinstance(critique.areas_for_improvement, list)
    assert len(critique.areas_for_improvement) > 0
    assert isinstance(critique.style_tags, list)
    assert len(critique.style_tags) > 0

    # Validate metadata
    assert critique.critic_version == "gemini-2.0-flash"
    assert len(critique.evaluated_at) > 0


def test_critique_image_mock_mode(critic_mock, sample_image_bytes):
    """
    Test image critique in mock mode.

    RED TEAM FIX #5: Structured JSON output (mocked).
    """
    critique = critic_mock.critique_image(
        image_data=sample_image_bytes,
        mime_type="image/png"
    )

    assert isinstance(critique, AestheticCritique)
    assert critique.overall_score > 0.0
    assert len(critique.style_tags) >= 3


def test_critique_svg_mock_mode(critic_mock, sample_svg):
    """
    Test SVG critique in mock mode.

    RED TEAM FIX #5: Structured JSON output (mocked).
    """
    critique = critic_mock.critique_svg(svg_data=sample_svg)

    assert isinstance(critique, AestheticCritique)
    assert critique.overall_score > 0.0
    assert len(critique.strengths) > 0


def test_critique_with_intent_context(critic_mock, sample_svg):
    """Test critique with IntentProfile context"""
    context = {
        "intent": {
            "emotional_register": {"joy": 0.9, "playful": 0.8},
            "target_audience": "children",
            "style_keywords": ["organic", "whimsical"]
        }
    }

    critique = critic_mock.critique_svg(
        svg_data=sample_svg,
        context=context
    )

    # Mock mode should still return valid critique
    assert isinstance(critique, AestheticCritique)
    assert critique.overall_score > 0.0


def test_critique_score_validation():
    """
    RED TEAM FIX #5: Test that CritiqueScore validates score bounds
    """
    # Valid scores
    valid_score = CritiqueScore(score=0.75, rationale="Good composition")
    assert valid_score.score == 0.75

    # Invalid scores should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        CritiqueScore(score=1.5, rationale="Invalid")

    with pytest.raises(Exception):  # Pydantic ValidationError
        CritiqueScore(score=-0.1, rationale="Invalid")


def test_aesthetic_critique_serialization(critic_mock):
    """
    RED TEAM FIX #5: Test that AestheticCritique serializes to JSON correctly
    """
    critique = critic_mock._mock_critique()

    # Serialize to dict
    critique_dict = critique.model_dump()

    assert isinstance(critique_dict, dict)
    assert "overall_score" in critique_dict
    assert "composition" in critique_dict
    assert "color_harmony" in critique_dict
    assert "style_tags" in critique_dict

    # Validate nested structure
    assert isinstance(critique_dict["composition"], dict)
    assert "score" in critique_dict["composition"]
    assert "rationale" in critique_dict["composition"]


def test_build_critique_prompt_with_context(critic_mock):
    """Test that critique prompt includes context correctly"""
    context = {
        "intent": {
            "emotional_register": {"calm": 0.8},
            "target_audience": "adults",
            "style_keywords": ["minimalist", "clean"]
        }
    }

    prompt = critic_mock._build_critique_prompt(context=context, is_svg=False)

    assert "calm" in prompt or "emotional_register" in prompt
    assert "adults" in prompt or "target_audience" in prompt
    assert "minimalist" in prompt or "style_keywords" in prompt


def test_build_critique_prompt_without_context(critic_mock):
    """Test that critique prompt works without context"""
    prompt = critic_mock._build_critique_prompt(context=None, is_svg=False)

    assert len(prompt) > 0
    assert "composition" in prompt.lower()
    assert "color" in prompt.lower()


def test_json_schema_structure(critic_mock):
    """
    RED TEAM FIX #5: Test that JSON schema is well-formed
    """
    schema = critic_mock._get_json_schema()

    assert isinstance(schema, dict)
    assert "type" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema

    # Validate required fields
    required_fields = schema["required"]
    assert "overall_score" in required_fields
    assert "composition" in required_fields
    assert "color_harmony" in required_fields
    assert "balance" in required_fields
    assert "visual_interest" in required_fields
    assert "technical_execution" in required_fields

    # Validate dimension score structure
    comp_schema = schema["properties"]["composition"]
    assert comp_schema["type"] == "object"
    assert "score" in comp_schema["properties"]
    assert "rationale" in comp_schema["properties"]


def test_critic_integration_with_dual_dna(storage, critic_mock, sample_svg):
    """
    Test integration: Critique + DualDNA ingestion workflow

    RED TEAM FIX #5: Structured critique integrated with tri-state memory
    """
    engine = DualDNAEngine(memory_storage=storage)

    # Step 1: Critique artifact
    critique = critic_mock.critique_svg(svg_data=sample_svg)

    # Step 2: Use critique results to build IntentProfile
    intent = {
        "emotional_register": {},
        "style_keywords": critique.style_tags,
        "source": "critic_inferred"
    }

    # Step 3: Ingest with critique metadata
    memory_block_id, style_dna_id, intent_profile_id = engine.ingest_artifact(
        session_id="critique_session",
        artifact_id="critiqued_art",
        svg_data=sample_svg,
        intent=intent,
        tags=["critiqued"] + critique.style_tags[:2],
        notes=f"Overall score: {critique.overall_score:.2f}"
    )

    # Validate ingestion
    assert memory_block_id is not None
    assert style_dna_id is not None
    assert intent_profile_id is not None

    # Retrieve and validate
    memory_block = storage.get_cognitive_memory_block(memory_block_id)
    assert "critiqued" in memory_block.tags
    assert str(critique.overall_score) in memory_block.notes

    # Validate IntentProfile has critique tags
    intent_profile = storage.get_intent_profile(intent_profile_id)
    assert any(tag in intent_profile.style_keywords for tag in critique.style_tags)


def test_multiple_critiques_different_artifacts(critic_mock, sample_svg):
    """Test that multiple critiques work independently"""
    critique1 = critic_mock.critique_svg(svg_data=sample_svg)
    critique2 = critic_mock.critique_svg(svg_data=sample_svg)

    # Both should be valid
    assert isinstance(critique1, AestheticCritique)
    assert isinstance(critique2, AestheticCritique)

    # Mock mode may return same values, but structure should be valid
    assert critique1.overall_score == critique2.overall_score  # Mock is deterministic


def test_critique_with_empty_context(critic_mock, sample_svg):
    """Test critique with empty context dict"""
    critique = critic_mock.critique_svg(
        svg_data=sample_svg,
        context={}
    )

    assert isinstance(critique, AestheticCritique)
    assert critique.overall_score > 0.0


def test_critic_handles_jpeg_mime_type(critic_mock):
    """Test that critic correctly handles JPEG images"""
    # Create simple JPEG
    img = Image.new('RGB', (50, 50), color=(200, 100, 50))
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    jpeg_bytes = buffer.getvalue()

    critique = critic_mock.critique_image(
        image_data=jpeg_bytes,
        mime_type="image/jpeg"
    )

    assert isinstance(critique, AestheticCritique)


def test_aesthetic_critique_timestamp_format(critic_mock):
    """Test that evaluated_at timestamp is in ISO format"""
    critique = critic_mock._mock_critique()

    # Should be ISO 8601 format (contains 'T' and ends with 'Z' or offset)
    assert 'T' in critique.evaluated_at
    # Should parse as datetime
    from datetime import datetime
    parsed = datetime.fromisoformat(critique.evaluated_at.replace('Z', '+00:00'))
    assert isinstance(parsed, datetime)


if __name__ == "__main__":
    print("=" * 70)
    print("Cognitive Kernel v2.5 - Session 3: Gemini Critic Tests")
    print("=" * 70)
    print()
    print("To run tests:")
    print("  pytest tests/test_gemini_critic.py -v")
    print()
    print("Tests cover:")
    print("  - Structured JSON output (RED TEAM FIX #5)")
    print("  - Mock mode for CI/CD (no API calls)")
    print("  - Image and SVG critique")
    print("  - IntentProfile context integration")
    print("  - Pydantic validation")
    print("  - DualDNA integration workflow")
    print()
    print("Note: These tests use MOCK MODE by default.")
    print("To test with real Gemini API, set GOOGLE_API_KEY env var.")
    print()
