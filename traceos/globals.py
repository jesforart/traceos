"""
TraceOS Global State

This module defines global state containers for the Iron Monolith.
Production implementation uses optimized in-memory structures.
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from traceos.sparks.registry import SparkRegistry
    from traceos.quantum.landscape import EnergyLandscape


# Global Spark Registry - initialized at startup
spark_registry: Optional["SparkRegistry"] = None

# Quantum Energy Landscape - initialized at startup
energy_landscape: Optional["EnergyLandscape"] = None


def get_spark_registry() -> "SparkRegistry":
    """Get the global Spark registry instance."""
    if spark_registry is None:
        raise RuntimeError("SparkRegistry not initialized. Call lifespan first.")
    return spark_registry


def get_energy_landscape() -> "EnergyLandscape":
    """Get the global energy landscape instance."""
    if energy_landscape is None:
        raise RuntimeError("EnergyLandscape not initialized. Call lifespan first.")
    return energy_landscape
