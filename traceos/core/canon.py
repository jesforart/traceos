"""
TraceOS System Canon

Defines the canonical mapping between biological metaphors and
systems-architecture vocabulary.

TraceOS is a BIOMIMETIC MODULAR MONOLITH:
- "Biomimetic": Uses biological metaphors as developer interface
- "Modular": Clean separation of concerns via Spark Organs
- "Monolith": Single runtime, no inter-service HTTP

DUAL-NAMING STRATEGY:
- Biological names (Brain, Gut, Eyes) = Developer/Artist UI
- Canonical names (CognitiveEngine, ValuationEngine) = Systems documentation

Both are FIRST-CLASS. Metaphors encode real architectural decisions.

@provenance traceos_core_v1
@organ kernel
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SystemRole(str, Enum):
    """Canonical system roles for TraceOS subsystems."""

    COGNITIVE_ENGINE = "cognitive_engine"
    VALUATION_ENGINE = "valuation_engine"
    MOTOR_CONTROLLER = "motor_controller"
    PERCEPTION_SERVICE = "perception_service"
    IDENTITY_MANAGER = "identity_manager"
    CONSOLIDATION_SERVICE = "consolidation_service"
    ANOMALY_DETECTOR = "anomaly_detector"
    SELF_MODEL_SERVICE = "self_model_service"


@dataclass(frozen=True)
class CanonicalSubsystem:
    """
    Maps a biological organ to its canonical systems-architecture definition.

    This is the Rosetta Stone of TraceOS: translate between metaphor and
    engineering vocabulary without losing either.
    """

    system_name: str  # e.g., "CognitiveEngine"
    biological_name: str  # e.g., "Brain"
    role: SystemRole
    responsibilities: tuple  # Immutable list of what this subsystem does
    guarantees: tuple  # Immutable list of system guarantees
    system_alias: str = ""  # Extended formal name


# =============================================================================
# THE TRACEOS CANON
# =============================================================================
# All 8 organs mapped to canonical definitions.
# This is the authoritative source for TraceOS architecture.
# =============================================================================

TRACEOS_CANON: tuple[CanonicalSubsystem, ...] = (
    # -------------------------------------------------------------------------
    # BRAIN → CognitiveEngine
    # -------------------------------------------------------------------------
    CanonicalSubsystem(
        system_name="CognitiveEngine",
        biological_name="Brain",
        role=SystemRole.COGNITIVE_ENGINE,
        system_alias="Logical Analysis Service",
        responsibilities=(
            "Evaluates logical correctness of derivations",
            "Analyzes architectural quality",
            "Tracks code organization patterns",
            "Manages fatigue from cognitive load",
        ),
        guarantees=(
            "Returns SparkReview within 100ms",
            "Fatigue bounded 0.0-1.0",
            "Deterministic scoring for identical inputs",
        ),
    ),
    # -------------------------------------------------------------------------
    # GUT → ValuationEngine
    # -------------------------------------------------------------------------
    CanonicalSubsystem(
        system_name="ValuationEngine",
        biological_name="Gut",
        role=SystemRole.VALUATION_ENGINE,
        system_alias="Heuristic Optimization Service",
        responsibilities=(
            "Evaluates emotional resonance and UX quality",
            "Detects technical debt markers",
            "Provides quantum stabilization for internal tension",
            "Resolves competing constraints via energy minimization",
        ),
        guarantees=(
            "Returns SparkReview within 100ms",
            "Mood state always defined",
            "Quantum jobs persisted to QuantumJobStore",
        ),
    ),
    # -------------------------------------------------------------------------
    # EYES → PerceptionService
    # -------------------------------------------------------------------------
    CanonicalSubsystem(
        system_name="PerceptionService",
        biological_name="Eyes",
        role=SystemRole.PERCEPTION_SERVICE,
        system_alias="Visual Analysis Pipeline",
        responsibilities=(
            "Detects visual content indicators",
            "Analyzes documentation quality",
            "Calibrates against DNA signatures",
            "Performs visual density analysis",
        ),
        guarantees=(
            "Returns SparkReview within 200ms",
            "DNA calibration non-blocking",
            "Graceful degradation without DNA",
        ),
    ),
    # -------------------------------------------------------------------------
    # SOUL → IdentityManager
    # -------------------------------------------------------------------------
    CanonicalSubsystem(
        system_name="IdentityManager",
        biological_name="Soul",
        role=SystemRole.IDENTITY_MANAGER,
        system_alias="Provenance Tracking Service",
        responsibilities=(
            "Validates provenance chains",
            "Checks TraceOS brand alignment",
            "Monitors DNA baseline presence",
            "Guards identity coherence",
        ),
        guarantees=(
            "Provenance node always validated",
            "Identity strength tracked",
            "Scoring deterministic",
        ),
    ),
    # -------------------------------------------------------------------------
    # DREAM → ConsolidationService
    # -------------------------------------------------------------------------
    CanonicalSubsystem(
        system_name="ConsolidationService",
        biological_name="Dream",
        role=SystemRole.CONSOLIDATION_SERVICE,
        system_alias="Memory Integration Service",
        responsibilities=(
            "Tracks DNA lineage growth",
            "Observes long-term creative evolution",
            "Identifies seasonal patterns",
            "Manages offline consolidation",
        ),
        guarantees=(
            "Non-judgmental baseline scoring",
            "Activation scales with lineage",
            "Never rejects derivations alone",
        ),
    ),
    # -------------------------------------------------------------------------
    # HANDS → MotorController
    # -------------------------------------------------------------------------
    CanonicalSubsystem(
        system_name="MotorController",
        biological_name="Hands",
        role=SystemRole.MOTOR_CONTROLLER,
        system_alias="Trajectory Generation Service",
        responsibilities=(
            "Tracks motor capability and fatigue",
            "Reports execution capacity",
            "Generates stroke trajectories",
            "Manages somatic state",
        ),
        guarantees=(
            "Capacity always bounded 0.1-1.0",
            "Fatigue accumulates at controlled rate",
            "Never blocks evaluation loop",
        ),
    ),
    # -------------------------------------------------------------------------
    # SHADOW → AnomalyDetector
    # -------------------------------------------------------------------------
    CanonicalSubsystem(
        system_name="AnomalyDetector",
        biological_name="Shadow",
        role=SystemRole.ANOMALY_DETECTOR,
        system_alias="System Health Monitor",
        responsibilities=(
            "Detects malformed derivations",
            "Monitors render corruption",
            "Tracks DNA identity drift",
            "Identifies behavioral anomalies",
        ),
        guarantees=(
            "All detectors run on every evaluation",
            "Critical anomalies cause rejection",
            "State reflects threat level",
        ),
    ),
    # -------------------------------------------------------------------------
    # IDENTITY → SelfModelService
    # -------------------------------------------------------------------------
    CanonicalSubsystem(
        system_name="SelfModelService",
        biological_name="Identity",
        role=SystemRole.SELF_MODEL_SERVICE,
        system_alias="Self-Awareness Service",
        responsibilities=(
            "Evaluates derivation alignment with TraceOS identity",
            "Integrates DNA alignment metrics",
            "Incorporates Shadow risk assessments",
            "Monitors organism architecture awareness",
        ),
        guarantees=(
            "Profile always buildable",
            "Shadow integration non-blocking",
            "Drift thresholds configurable",
        ),
    ),
)


# =============================================================================
# LOOKUP FUNCTIONS
# =============================================================================


def get_subsystem_by_biological_name(name: str) -> Optional[CanonicalSubsystem]:
    """
    Look up a subsystem by its biological name (Brain, Gut, etc.).

    Case-insensitive matching.
    """
    name_lower = name.lower()
    for subsystem in TRACEOS_CANON:
        if subsystem.biological_name.lower() == name_lower:
            return subsystem
    return None


def get_subsystem_by_system_name(name: str) -> Optional[CanonicalSubsystem]:
    """
    Look up a subsystem by its canonical system name (CognitiveEngine, etc.).

    Case-insensitive matching.
    """
    name_lower = name.lower()
    for subsystem in TRACEOS_CANON:
        if subsystem.system_name.lower() == name_lower:
            return subsystem
    return None
