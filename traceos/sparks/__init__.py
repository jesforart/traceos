"""
TraceOS Spark Organ System

Self-maintaining cognitive organs with persistent state.
Phase 4: Added DreamSpark for long-term consolidation.

@provenance traceos_sparks_v1
@organ kernel
"""

import logging

from .registry import registry
from .organs.brain import BrainSpark
from .organs.gut import GutSpark
from .organs.eyes import EyesSpark
from .organs.soul import SoulSpark
from .organs.dream import DreamSpark

logger = logging.getLogger(__name__)


# Auto-register core Sparks on module import
def _initialize_core_sparks():
    """Initialize and register the 5 core Sparks."""
    brain = BrainSpark()
    gut = GutSpark()
    eyes = EyesSpark()
    soul = SoulSpark()
    dream = DreamSpark()

    registry.register(brain)
    registry.register(gut)
    registry.register(eyes)
    registry.register(soul)
    registry.register(dream)

    logger.info("Core Sparks initialized: Brain, Gut, Eyes, Soul, Dream")


# Initialize on import
_initialize_core_sparks()

__all__ = ["registry", "BrainSpark", "GutSpark", "EyesSpark", "SoulSpark", "DreamSpark"]
