"""
TraceOS Spark Organs Module

The Spark Organ architecture provides specialized cognitive modules
that maintain persistent state and collaborate through the Protocol Kernel.

Six Spark Organs:
    - Brain: Logic, reasoning, architectural decisions
    - Gut: Emotional valuation, taste, intuition
    - Eyes: Perception, stroke quality analysis
    - Hands: Motor control, stroke planning
    - Soul: Provenance tracking, DNA alignment
    - Dream: Long-term memory integration
"""

from traceos.sparks.base import SparkBase
from traceos.sparks.registry import SparkRegistry
from traceos.sparks.schemas import SparkMetadata, SparkState

__all__ = [
    "SparkBase",
    "SparkRegistry",
    "SparkMetadata",
    "SparkState",
]
