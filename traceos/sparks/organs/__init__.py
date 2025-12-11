"""
TraceOS Spark Organs

Concrete implementations of the six cognitive organs.
Production implementations contain proprietary neural architectures.
"""

from traceos.sparks.organs.brain import BrainSpark
from traceos.sparks.organs.gut import GutSpark
from traceos.sparks.organs.eyes import EyesSpark
from traceos.sparks.organs.hands import HandsSpark
from traceos.sparks.organs.soul import SoulSpark
from traceos.sparks.organs.dream import DreamSpark

__all__ = [
    "BrainSpark",
    "GutSpark",
    "EyesSpark",
    "HandsSpark",
    "SoulSpark",
    "DreamSpark",
]
