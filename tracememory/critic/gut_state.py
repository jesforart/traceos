"""
GutCritic — The Gut's Valuation Engine

The Gut tastes interaction events and derives emotional state.
This organ FEELS — it does not think. It senses micro-reactions
and translates them into frustration, flow, and mood.

Taste metaphors:
- Rapid undos taste bitter (frustration)
- Smooth acceptance tastes sweet (flow)
- Erratic chaos tastes acrid (route to Shadow)

@provenance intent_gut_taste_001
@organ valuation
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Deque, Optional, Dict, Any
import logging

from .models.gut_state import GutState, MoodState, ResonanceEvent

logger = logging.getLogger(__name__)


class OrganBoundaryViolation(Exception):
    """
    Raised when a non-Valuation organ attempts to mutate GutState.

    CONSTRAINT: Only the Valuation organ may write to GutState.
    This prevents self-amplifying mood spirals.
    """
    pass


class GutCritic:
    """
    The Gut tastes interaction events and derives emotional state.

    This organ FEELS — it does not think. It senses micro-reactions
    and translates them into frustration, flow, and mood.

    Usage:
        critic = GutCritic()
        critic.ingest_batch(events)
        state = critic.state  # Read-only access

    CONSTRAINTS:
    - max_events: Rolling window size (memory bounded)
    - decay: Exponential decay factor for emotional signals
    - min_dwell_time: Minimum time before mood can transition (2s)
    """

    def __init__(
        self,
        max_events: int = 100,
        decay: float = 0.95,
        min_dwell_time_seconds: float = 2.0
    ) -> None:
        """
        Initialize the Gut's sensory apparatus.

        Args:
            max_events: Maximum events in rolling window (default 100)
            decay: Exponential decay factor (default 0.95)
            min_dwell_time_seconds: Minimum dwell time before mood transition (default 2.0)
        """
        self._events: Deque[ResonanceEvent] = deque(maxlen=max_events)
        self._state = GutState(
            mood=MoodState.CALM,
            frustration_index=0.0,
            flow_probability=0.0,
            last_updated=datetime.utcnow(),
        )
        self._decay = decay
        self._min_dwell_time = timedelta(seconds=min_dwell_time_seconds)
        self._last_mood_change: datetime = datetime.utcnow()
        self._chaos_start: Optional[datetime] = None
        self._erratic_event_times: Deque[datetime] = deque(maxlen=10)

    @property
    def state(self) -> GutState:
        """
        Read-only access to GutState for other organs.

        CONSTRAINT: This is the only public accessor.
        Mutations only via ingest_batch().
        """
        return self._state

    def _sense_frustration(self, events: list[ResonanceEvent]) -> float:
        """
        Taste the bitterness of rapid undos and rejections.

        The Gut recoils from:
        - Rapid undo after suggestion (<500ms) — bitter taste
        - Ghost rejection — sour note
        - Stroke rejection — mild bitterness

        Uses exponential moving average with decay.
        """
        frustration = self._state.frustration_index * self._decay

        for ev in events:
            # Rapid undo after suggestion = bitter taste
            if ev.type == "undo" and ev.latency_ms is not None:
                if ev.latency_ms < 500:
                    # Very fast undo — sharp bitterness
                    frustration += 0.10
                    logger.debug(f"[Gut] Tasted bitter undo: {ev.latency_ms}ms")
                elif ev.latency_ms < 1000:
                    # Moderate undo — mild bitterness
                    frustration += 0.05

            # Ghost rejection = sour note
            if ev.type == "ghost_reject":
                frustration += 0.08
                logger.debug("[Gut] Tasted sour ghost rejection")

            # Stroke rejection = mild bitterness
            if ev.type == "stroke_reject":
                frustration += 0.05

        # Clamp to [0, 1]
        return max(0.0, min(1.0, frustration))

    def _sense_flow(self, events: list[ResonanceEvent]) -> float:
        """
        Taste the sweetness of smooth acceptance and sustained work.

        The Gut savors:
        - Fast acceptance (<200ms) — sweet taste
        - Ghost acceptance — harmonious note
        - Pauses after acceptance — satisfied settling

        Uses exponential moving average with decay.
        """
        flow = self._state.flow_probability * self._decay

        for ev in events:
            # Fast acceptance = sweet taste
            if ev.type in ("stroke_accept", "ghost_accept"):
                if ev.latency_ms is not None and ev.latency_ms < 200:
                    # Very fast acceptance — sweet delight
                    flow += 0.12
                    logger.debug(f"[Gut] Savored sweet acceptance: {ev.latency_ms}ms")
                else:
                    # Normal acceptance — pleasant taste
                    flow += 0.05

            # Pause after work = satisfied settling
            if ev.type == "pause_detected":
                # Small flow boost — the artist is contemplating
                flow += 0.03

        # Clamp to [0, 1]
        return max(0.0, min(1.0, flow))

    def _check_erratic_input(self, events: list[ResonanceEvent]) -> bool:
        """
        Detect erratic input patterns that might indicate Chaos.

        Chaos triggers:
        - erratic_input flag set on event
        - 10 erratic events in 5 seconds
        """
        now = datetime.utcnow()

        for ev in events:
            if ev.erratic_input:
                self._erratic_event_times.append(now)

        # Check for 10 erratic events in 5 seconds
        if len(self._erratic_event_times) >= 10:
            oldest = self._erratic_event_times[0]
            if (now - oldest).total_seconds() <= 5.0:
                return True

        return any(ev.erratic_input for ev in events if ev.erratic_input)

    def _derive_mood(
        self,
        frustration: float,
        flow: float,
        has_erratic: bool
    ) -> MoodState:
        """
        The Gut intuits the overall mood from taste signals.

        Mood derivation (per spec):
        - Chaos: frustration > 0.8 AND erratic for >10s
        - Frustration: frustration > 0.7 (when not Chaos)
        - Flow: flow > 0.8
        - Exploration: flow 0.5-0.8 AND low frustration
        - Calm: default (low frustration, low-moderate flow)

        Includes hysteresis: minimum 2s dwell time prevents jitter.
        """
        now = datetime.utcnow()

        # Check hysteresis — can we transition?
        time_since_last_change = now - self._last_mood_change
        can_transition = time_since_last_change >= self._min_dwell_time

        # Chaos detection: high frustration + erratic input for >10s
        if frustration > 0.8 and has_erratic:
            if self._chaos_start is None:
                self._chaos_start = now
                logger.info("[Gut] Chaos building — erratic + high frustration")
            elif (now - self._chaos_start).total_seconds() > 10:
                if can_transition or self._state.mood == MoodState.CHAOS:
                    self._last_mood_change = now
                    logger.warning("[Gut] CHAOS — routing to Shadow")
                    return MoodState.CHAOS
        else:
            self._chaos_start = None

        # Don't transition if hysteresis not met
        if not can_transition:
            return self._state.mood

        # Frustration: sustained bitterness
        if frustration > 0.7:
            if self._state.mood != MoodState.FRUSTRATION:
                self._last_mood_change = now
                logger.info(f"[Gut] Frustration detected: {frustration:.2f}")
            return MoodState.FRUSTRATION

        # Flow: sustained sweetness
        if flow > 0.8:
            if self._state.mood != MoodState.FLOW:
                self._last_mood_change = now
                logger.info(f"[Gut] Flow state achieved: {flow:.2f}")
            return MoodState.FLOW

        # Exploration: moderate flow with variety
        if 0.5 <= flow <= 0.8 and frustration < 0.4:
            if self._state.mood != MoodState.EXPLORATION:
                self._last_mood_change = now
                logger.info(f"[Gut] Exploration mode: flow={flow:.2f}, frustration={frustration:.2f}")
            return MoodState.EXPLORATION

        # Default: Calm
        if self._state.mood != MoodState.CALM:
            self._last_mood_change = now
            logger.debug("[Gut] Returning to Calm")
        return MoodState.CALM

    def ingest_batch(self, events: list[ResonanceEvent]) -> GutState:
        """
        The Gut tastes a batch of interaction events.

        This is the ONLY mutation method. All state changes
        flow through here.

        Args:
            events: Batch of ResonanceEvents to process

        Returns:
            Updated GutState
        """
        if not events:
            return self._state

        # Add events to rolling window
        for ev in events:
            self._events.append(ev)

        # Sense the emotional signals
        has_erratic = self._check_erratic_input(events)
        frustration = self._sense_frustration(events)
        flow = self._sense_flow(events)
        mood = self._derive_mood(frustration, flow, has_erratic)

        # Update state
        self._state = GutState(
            mood=mood,
            frustration_index=frustration,
            flow_probability=flow,
            last_updated=datetime.utcnow(),
        )

        return self._state

    def clear(self) -> None:
        """
        Clear all emotional state.

        Called on session end — no emotional surveillance.
        Mood data cleared per sovereignty requirements.
        """
        self._events.clear()
        self._erratic_event_times.clear()
        self._chaos_start = None
        self._state = GutState(
            mood=MoodState.CALM,
            frustration_index=0.0,
            flow_probability=0.0,
            last_updated=datetime.utcnow(),
        )
        self._last_mood_change = datetime.utcnow()
        logger.info("[Gut] State cleared — session ended")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for API responses."""
        return {
            "mood": self._state.mood.value,
            "frustrationIndex": self._state.frustration_index,
            "flowProbability": self._state.flow_probability,
            "lastUpdated": self._state.last_updated.isoformat(),
        }
