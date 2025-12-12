"""
TraceOS Spark Organs Module

The Spark Organ architecture provides specialized cognitive modules
that maintain persistent state and collaborate through the Protocol Kernel.

Eight Spark Organs:
    - Brain: Logic, reasoning, architectural decisions
    - Gut: Emotional valuation, taste, intuition
    - Eyes: Perception, stroke quality analysis
    - Hands: Motor control, stroke planning
    - Soul: Provenance tracking, DNA alignment
    - Dream: Long-term memory integration
    - Shadow: Anomaly detection, integrity assurance
    - Identity: Self-model, alignment guardian

Rosetta Layer:
    Technical aliases map biological names to systems-architecture vocabulary.
    Both naming schemes are first-class citizens.
"""

from traceos.sparks.base import SparkBase
from traceos.sparks.registry import SparkRegistry
from traceos.sparks.schemas import SparkMetadata, SparkState

# Import Spark organs
from traceos.sparks.organs.brain import BrainSpark
from traceos.sparks.organs.gut import GutSpark
from traceos.sparks.organs.eyes import EyesSpark
from traceos.sparks.organs.hands import HandsSpark
from traceos.sparks.organs.soul import SoulSpark
from traceos.sparks.organs.dream import DreamSpark

# =============================================================================
# ROSETTA LAYER: Technical Aliases
# =============================================================================
# These aliases allow engineers to import using systems-architecture vocabulary
# while the biological names remain the canonical internal implementation.
#
# Usage:
#   from traceos.sparks import CognitiveEngine  # Same as BrainSpark
#   from traceos.sparks import ValuationEngine  # Same as GutSpark
# =============================================================================

CognitiveEngine = BrainSpark
ValuationEngine = GutSpark
PerceptionService = EyesSpark
MotorController = HandsSpark
IdentityManager = SoulSpark
ConsolidationService = DreamSpark

# Shadow and Identity Sparks (stubs in public repo)
# Full implementations are in traceos-core (private)
try:
    from traceos.shadow.spark import ShadowSpark
    AnomalyDetector = ShadowSpark
except ImportError:
    ShadowSpark = None
    AnomalyDetector = None

try:
    from traceos.sparks.organs.identity import IdentitySpark
    SelfModelService = IdentitySpark
except ImportError:
    IdentitySpark = None
    SelfModelService = None

__all__ = [
    # Core
    "SparkBase",
    "SparkRegistry",
    "SparkMetadata",
    "SparkState",
    # Biological Names (Primary)
    "BrainSpark",
    "GutSpark",
    "EyesSpark",
    "HandsSpark",
    "SoulSpark",
    "DreamSpark",
    "ShadowSpark",
    "IdentitySpark",
    # Technical Aliases (Rosetta Layer)
    "CognitiveEngine",
    "ValuationEngine",
    "PerceptionService",
    "MotorController",
    "IdentityManager",
    "ConsolidationService",
    "AnomalyDetector",
    "SelfModelService",
]
