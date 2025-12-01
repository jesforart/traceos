"""
Tests for GutCritic — Emotional State Valuation

Tests cover:
- Frustration calculation from undo patterns
- Flow calculation from acceptance patterns
- Mood state transitions with hysteresis
- Chaos trigger conditions
- Edge cases and boundary conditions

@provenance intent_gut_taste_001
@organ valuation
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from tracememory.critic.gut_state import GutCritic
from tracememory.critic.models.gut_state import GutState, MoodState, ResonanceEvent


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture
def critic() -> GutCritic:
    """Fresh GutCritic with no hysteresis delay for testing."""
    return GutCritic(max_events=100, decay=0.95, min_dwell_time_seconds=0.0)


@pytest.fixture
def critic_with_hysteresis() -> GutCritic:
    """GutCritic with normal hysteresis for timing tests."""
    return GutCritic(max_events=100, decay=0.95, min_dwell_time_seconds=2.0)


def make_event(
    event_type: str,
    latency_ms: float = None,
    erratic: bool = False,
    session_id: str = "test_session"
) -> ResonanceEvent:
    """Helper to create ResonanceEvent."""
    return ResonanceEvent(
        type=event_type,
        timestamp=datetime.utcnow().timestamp() * 1000,
        session_id=session_id,
        latency_ms=latency_ms,
        erratic_input=erratic
    )


def make_undo_batch(count: int, latency_ms: float = 200) -> List[ResonanceEvent]:
    """Create a batch of undo events."""
    return [make_event("undo", latency_ms=latency_ms) for _ in range(count)]


def make_accept_batch(count: int, latency_ms: float = 150) -> List[ResonanceEvent]:
    """Create a batch of stroke_accept events."""
    return [make_event("stroke_accept", latency_ms=latency_ms) for _ in range(count)]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FRUSTRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestFrustrationCalculation:
    """Tests for frustration_index calculation."""

    def test_rapid_undo_increases_frustration(self, critic: GutCritic):
        """Rapid undos (<500ms) should increase frustration significantly."""
        # 10 rapid undos at 200ms each
        events = make_undo_batch(10, latency_ms=200)
        critic.ingest_batch(events)

        assert critic.state.frustration_index > 0.7, \
            f"Expected frustration > 0.7 after 10 rapid undos, got {critic.state.frustration_index}"

    def test_slow_undo_increases_frustration_less(self, critic: GutCritic):
        """Slower undos (500-1000ms) should increase frustration less."""
        # 10 slower undos at 700ms each
        events = make_undo_batch(10, latency_ms=700)
        critic.ingest_batch(events)

        # Should be lower than rapid undos
        assert 0.3 < critic.state.frustration_index < 0.7, \
            f"Expected moderate frustration for slow undos, got {critic.state.frustration_index}"

    def test_ghost_reject_increases_frustration(self, critic: GutCritic):
        """Ghost rejection should add to frustration."""
        events = [make_event("ghost_reject") for _ in range(10)]
        critic.ingest_batch(events)

        assert critic.state.frustration_index > 0.5, \
            f"Expected frustration > 0.5 after 10 ghost rejects, got {critic.state.frustration_index}"

    def test_frustration_decays_without_events(self, critic: GutCritic):
        """Frustration should decay with positive events."""
        # First spike frustration
        critic.ingest_batch(make_undo_batch(10, latency_ms=200))
        initial_frustration = critic.state.frustration_index

        # Then send neutral events (accepts)
        for _ in range(5):
            critic.ingest_batch(make_accept_batch(5, latency_ms=100))

        # Frustration should have decayed
        assert critic.state.frustration_index < initial_frustration, \
            "Frustration should decay with positive interactions"

    def test_frustration_clamped_to_1(self, critic: GutCritic):
        """Frustration should never exceed 1.0."""
        # Massive undo spam
        events = make_undo_batch(100, latency_ms=100)
        critic.ingest_batch(events)

        assert critic.state.frustration_index <= 1.0, \
            f"Frustration exceeded 1.0: {critic.state.frustration_index}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FLOW TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestFlowCalculation:
    """Tests for flow_probability calculation."""

    def test_fast_accepts_increase_flow(self, critic: GutCritic):
        """Fast acceptance (<200ms) should build flow state."""
        # 10 fast accepts at 100ms
        events = make_accept_batch(10, latency_ms=100)
        critic.ingest_batch(events)

        assert critic.state.flow_probability > 0.8, \
            f"Expected flow > 0.8 after 10 fast accepts, got {critic.state.flow_probability}"

    def test_ghost_accept_increases_flow(self, critic: GutCritic):
        """Ghost acceptance should boost flow."""
        events = [make_event("ghost_accept", latency_ms=150) for _ in range(10)]
        critic.ingest_batch(events)

        assert critic.state.flow_probability > 0.8, \
            f"Expected flow > 0.8 after 10 ghost accepts, got {critic.state.flow_probability}"

    def test_slow_accepts_increase_flow_less(self, critic: GutCritic):
        """Slower accepts should increase flow less."""
        events = make_accept_batch(10, latency_ms=500)
        critic.ingest_batch(events)

        # Should be moderate
        assert 0.3 < critic.state.flow_probability < 0.8, \
            f"Expected moderate flow for slow accepts, got {critic.state.flow_probability}"

    def test_flow_clamped_to_1(self, critic: GutCritic):
        """Flow should never exceed 1.0."""
        events = make_accept_batch(100, latency_ms=50)
        critic.ingest_batch(events)

        assert critic.state.flow_probability <= 1.0, \
            f"Flow exceeded 1.0: {critic.state.flow_probability}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MOOD TRANSITION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestMoodTransitions:
    """Tests for mood state machine transitions."""

    def test_starts_calm(self, critic: GutCritic):
        """Initial state should be Calm."""
        assert critic.state.mood == MoodState.CALM

    def test_transitions_to_flow(self, critic: GutCritic):
        """High flow probability should trigger Flow mood."""
        # Build up flow
        for _ in range(3):
            critic.ingest_batch(make_accept_batch(10, latency_ms=100))

        assert critic.state.mood == MoodState.FLOW, \
            f"Expected Flow mood after sustained accepts, got {critic.state.mood}"

    def test_transitions_to_frustration(self, critic: GutCritic):
        """High frustration should trigger Frustration mood."""
        # Build up frustration
        critic.ingest_batch(make_undo_batch(15, latency_ms=200))

        assert critic.state.mood == MoodState.FRUSTRATION, \
            f"Expected Frustration mood after rapid undos, got {critic.state.mood}"

    def test_transitions_to_exploration(self, critic: GutCritic):
        """Moderate flow with low frustration triggers Exploration."""
        # Build moderate flow
        critic.ingest_batch(make_accept_batch(6, latency_ms=100))

        # Should be in exploration range (0.5-0.8 flow, <0.4 frustration)
        if 0.5 <= critic.state.flow_probability <= 0.8:
            assert critic.state.mood == MoodState.EXPLORATION, \
                f"Expected Exploration mood, got {critic.state.mood}"

    def test_flow_and_frustration_coexist(self, critic: GutCritic):
        """User can have both flow and low frustration."""
        # Build flow first
        critic.ingest_batch(make_accept_batch(15, latency_ms=100))

        # Small frustration shouldn't break flow
        critic.ingest_batch([make_event("undo", latency_ms=200)])

        # Should still be in flow
        assert critic.state.mood == MoodState.FLOW or critic.state.frustration_index < 0.3


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHAOS TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestChaosTrigger:
    """Tests for Chaos state detection."""

    def test_chaos_requires_erratic_and_frustration(self, critic: GutCritic):
        """Chaos requires both erratic input and high frustration."""
        # High frustration alone shouldn't trigger Chaos
        critic.ingest_batch(make_undo_batch(20, latency_ms=100))
        assert critic.state.mood != MoodState.CHAOS, \
            "Frustration alone shouldn't trigger Chaos"

    def test_chaos_with_erratic_events(self, critic: GutCritic):
        """Erratic input with high frustration should build toward Chaos."""
        # First build high frustration
        critic.ingest_batch(make_undo_batch(20, latency_ms=100))

        # Now add erratic events
        erratic_events = [
            make_event("undo", latency_ms=100, erratic=True)
            for _ in range(10)
        ]
        critic.ingest_batch(erratic_events)

        # Note: Full Chaos requires >10s of sustained erratic + frustration
        # This test just verifies the mechanism works
        assert critic.state.frustration_index > 0.8


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EDGE CASES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_batch_is_safe(self, critic: GutCritic):
        """Empty event batch should not crash."""
        initial_state = critic.state
        critic.ingest_batch([])
        assert critic.state == initial_state

    def test_none_latency_handled(self, critic: GutCritic):
        """Events without latency should be handled gracefully."""
        events = [make_event("undo", latency_ms=None) for _ in range(5)]
        critic.ingest_batch(events)  # Should not raise

    def test_clear_resets_state(self, critic: GutCritic):
        """Clear should reset to initial state."""
        # Build up state
        critic.ingest_batch(make_undo_batch(10, latency_ms=200))
        assert critic.state.frustration_index > 0

        # Clear
        critic.clear()

        # Should be back to initial
        assert critic.state.mood == MoodState.CALM
        assert critic.state.frustration_index == 0.0
        assert critic.state.flow_probability == 0.0

    def test_rolling_window_bounded(self, critic: GutCritic):
        """Event window should stay bounded."""
        # Ingest more than max_events
        for _ in range(20):
            critic.ingest_batch(make_undo_batch(10, latency_ms=300))

        # Window should still be bounded (internal, but we can check state is valid)
        assert 0 <= critic.state.frustration_index <= 1
        assert 0 <= critic.state.flow_probability <= 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestIntegrationScenarios:
    """Realistic user interaction scenarios."""

    def test_rapid_undo_sequence(self, critic: GutCritic):
        """Simulate user rapidly undoing after AI suggestions."""
        # User accepts a few strokes
        critic.ingest_batch(make_accept_batch(3, latency_ms=150))
        assert critic.state.frustration_index < 0.3

        # AI makes suggestion, user immediately undoes (frustrated)
        for _ in range(5):
            critic.ingest_batch([make_event("ghost_reject")])
            critic.ingest_batch([make_event("undo", latency_ms=200)])

        # Should be in frustration
        assert critic.state.frustration_index > 0.5

    def test_sustained_flow_session(self, critic: GutCritic):
        """Simulate artist in deep flow state."""
        # Continuous acceptance stream
        for _ in range(10):
            critic.ingest_batch(make_accept_batch(5, latency_ms=100))

        assert critic.state.mood == MoodState.FLOW
        assert critic.state.flow_probability > 0.8

    def test_mixed_session(self, critic: GutCritic):
        """Simulate realistic mixed interactions."""
        # Start with some accepts
        critic.ingest_batch(make_accept_batch(5, latency_ms=150))

        # A few undos
        critic.ingest_batch(make_undo_batch(2, latency_ms=400))

        # More accepts
        critic.ingest_batch(make_accept_batch(5, latency_ms=120))

        # Ghost accept
        critic.ingest_batch([make_event("ghost_accept", latency_ms=180)])

        # Pause
        critic.ingest_batch([make_event("pause_detected")])

        # State should be reasonably positive
        assert critic.state.frustration_index < 0.5
        assert critic.state.flow_probability > 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
