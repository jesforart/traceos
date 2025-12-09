"""
TraceOS Core Organs

Brain, Gut, Eyes, Soul, Dream, Hands - The six pillars of TraceOS.

Phase 5: Added Hands (somatic organ for motor expression).

@provenance traceos_sparks_v1
"""

from .brain import BrainSpark
from .gut import GutSpark
from .eyes import EyesSpark
from .soul import SoulSpark
from .dream import DreamSpark
from .hands import HandsSpark

__all__ = ["BrainSpark", "GutSpark", "EyesSpark", "SoulSpark", "DreamSpark", "HandsSpark"]
