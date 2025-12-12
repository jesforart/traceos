"""
TraceOS Core Module - System Canon Layer

Provides the canonical mapping between biological metaphors
and systems-architecture vocabulary.

Architecture: Biomimetic Modular Monolith

@provenance traceos_core_v1
@organ kernel
"""

from traceos.core.canon import (
    SystemRole,
    CanonicalSubsystem,
    TRACEOS_CANON,
    get_subsystem_by_biological_name,
    get_subsystem_by_system_name,
)

__all__ = [
    "SystemRole",
    "CanonicalSubsystem",
    "TRACEOS_CANON",
    "get_subsystem_by_biological_name",
    "get_subsystem_by_system_name",
]
