"""
Constraint Engine — Brain's Interface to Gut Emotional State

The Brain reads the Gut's emotional state and adjusts its behavior.
This is a one-way flow: Gut → Brain. The Brain NEVER writes to GutState.

High frustration = quieter, more conservative suggestions
Deep flow = bolder, more exploratory suggestions
Chaos = dramatic reduction (route to Shadow if available)

CROSS-ORGAN CONSTRAINT:
This function READS GutState. It NEVER WRITES.
Cross-organ mutation is forbidden to prevent self-amplifying mood spirals.

@provenance intent_gut_taste_001
@organ cognitive (reads from valuation)
"""

import logging
from typing import Optional

# Import GutState models (read-only access)
from tracememory.critic.models.gut_state import GutState, MoodState

logger = logging.getLogger(__name__)


def adjust_creativity(
    base_temperature: float,
    gut: Optional[GutState]
) -> float:
    """
    The Brain reads the Gut's emotional state and adjusts its behavior.

    High frustration = quieter, more conservative suggestions.
    Deep flow = bolder, more exploratory suggestions.
    Chaos = dramatic reduction (Shadow handling).

    CONSTRAINT: This function READS GutState. It NEVER WRITES.
    Cross-organ mutation is forbidden.

    Args:
        base_temperature: Base creativity temperature (typically 0.7-1.0)
        gut: Current GutState (optional, defaults to neutral if None)

    Returns:
        Adjusted temperature value (clamped to 0.1-2.0)

    Examples:
        >>> adjust_creativity(0.7, gut_with_high_frustration)
        0.35  # 50% reduction
        >>> adjust_creativity(0.7, gut_in_flow)
        0.91  # 30% boost
    """
    if gut is None:
        # No Gut data available — use base temperature unchanged
        logger.debug("[Brain] No GutState available, using base temperature")
        return base_temperature

    temp = base_temperature

    # Frustration throttles creativity (bitter taste → quieter suggestions)
    if gut.frustration_index > 0.7:
        temp *= 0.5  # 50% reduction
        logger.info(
            f"[Brain] Frustration detected ({gut.frustration_index:.2f}) "
            f"— reducing creativity by 50%"
        )

    # Flow encourages exploration (sweet taste → bolder suggestions)
    if gut.flow_probability > 0.8:
        temp *= 1.3  # 30% boost
        logger.info(
            f"[Brain] Flow detected ({gut.flow_probability:.2f}) "
            f"— increasing exploration by 30%"
        )

    # Chaos routes to Shadow (if available)
    # Brain just backs off dramatically during Chaos
    if gut.mood == MoodState.CHAOS:
        temp *= 0.3  # Dramatic reduction
        logger.warning(
            "[Brain] CHAOS detected — dramatic creativity reduction. "
            "Shadow routing recommended."
        )

    # Exploration mode — moderate boost
    if gut.mood == MoodState.EXPLORATION and gut.frustration_index < 0.4:
        temp *= 1.15  # 15% boost for exploration
        logger.debug("[Brain] Exploration mode — slight creativity boost")

    # Clamp to safe range
    result = max(0.1, min(2.0, temp))

    logger.debug(
        f"[Brain] Creativity adjusted: {base_temperature:.2f} → {result:.2f} "
        f"(mood={gut.mood.value}, frustration={gut.frustration_index:.2f}, flow={gut.flow_probability:.2f})"
    )

    return result


def adjust_style_distance(
    base_max_distance: float,
    gut: Optional[GutState]
) -> float:
    """
    Adjust the maximum allowed style distance based on Gut state.

    In flow state, the artist is receptive to more variation.
    In frustration, suggestions should stay closer to established style.

    CONSTRAINT: This function READS GutState. It NEVER WRITES.

    Args:
        base_max_distance: Base style distance threshold (typically 0.25-0.30)
        gut: Current GutState (optional)

    Returns:
        Adjusted maximum style distance (clamped to 0.1-0.5)
    """
    if gut is None:
        return base_max_distance

    distance = base_max_distance

    # Flow increases tolerance for style exploration
    if gut.flow_probability > 0.8:
        distance *= 1.3  # 30% increase in allowed variation
        logger.debug(
            f"[Brain] Flow state — expanding style distance allowance to {distance:.2f}"
        )

    # Frustration decreases tolerance
    if gut.frustration_index > 0.7:
        distance *= 0.7  # 30% decrease — stay closer to known style
        logger.debug(
            f"[Brain] Frustration — restricting style distance to {distance:.2f}"
        )

    # Exploration mode — moderate increase
    if gut.mood == MoodState.EXPLORATION:
        distance *= 1.2
        logger.debug(
            f"[Brain] Exploration mode — style distance allowance: {distance:.2f}"
        )

    # Clamp to reasonable range
    return max(0.1, min(0.5, distance))


def should_route_to_shadow(gut: Optional[GutState]) -> bool:
    """
    Determine if the current emotional state warrants Shadow routing.

    Chaos state triggers Shadow routing for alternative processing.
    The Shadow organ handles extreme states with different creativity.

    CONSTRAINT: This function READS GutState. It NEVER WRITES.

    Args:
        gut: Current GutState

    Returns:
        True if Shadow routing is recommended
    """
    if gut is None:
        return False

    if gut.mood == MoodState.CHAOS:
        logger.info("[Brain] Recommending Shadow routing — Chaos state detected")
        return True

    # Extended high frustration (>0.9) might also benefit from Shadow
    if gut.frustration_index > 0.9:
        logger.info("[Brain] Recommending Shadow routing — extreme frustration")
        return True

    return False


class ConstraintContext:
    """
    Context object for Brain decisions that incorporates Gut state.

    Use this to pass emotional context through the orchestration pipeline.

    Example:
        ctx = ConstraintContext(gut_state=current_gut)
        temperature = ctx.get_creativity_temperature(base=0.7)
        max_distance = ctx.get_style_distance_max(base=0.25)
    """

    def __init__(self, gut_state: Optional[GutState] = None):
        """
        Initialize constraint context with optional Gut state.

        Args:
            gut_state: Current GutState from the valuation organ
        """
        self._gut = gut_state

    @property
    def gut(self) -> Optional[GutState]:
        """Read-only access to Gut state."""
        return self._gut

    @property
    def mood(self) -> Optional[MoodState]:
        """Current mood state."""
        return self._gut.mood if self._gut else None

    @property
    def frustration(self) -> float:
        """Current frustration index (0.0 if no Gut)."""
        return self._gut.frustration_index if self._gut else 0.0

    @property
    def flow(self) -> float:
        """Current flow probability (0.0 if no Gut)."""
        return self._gut.flow_probability if self._gut else 0.0

    def get_creativity_temperature(self, base: float = 0.7) -> float:
        """Get adjusted creativity temperature."""
        return adjust_creativity(base, self._gut)

    def get_style_distance_max(self, base: float = 0.25) -> float:
        """Get adjusted maximum style distance."""
        return adjust_style_distance(base, self._gut)

    def should_use_shadow(self) -> bool:
        """Check if Shadow routing is recommended."""
        return should_route_to_shadow(self._gut)
