"""
Spark Registry

Singleton registry for all TraceOS cognitive organs.

@provenance traceos_sparks_v1
@organ kernel
"""

import logging
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import SparkBase

logger = logging.getLogger(__name__)


class SparkRegistry:
    """
    Singleton registry managing all Spark organs.

    Sparks self-register on import, creating a living
    nervous system that evolves with the codebase.
    """

    def __init__(self):
        self._sparks: Dict[str, "SparkBase"] = {}
        logger.info("Spark Registry initialized")

    def register(self, spark: "SparkBase") -> None:
        """
        Register a Spark organ.

        Args:
            spark: Spark instance to register
        """
        name = spark.metadata.name
        self._sparks[name] = spark
        logger.info(f"Registered {name} Spark ({spark.metadata.organ_type})")

    def get(self, name: str) -> "SparkBase | None":
        """Get a Spark by name."""
        return self._sparks.get(name)

    def get_all(self) -> List["SparkBase"]:
        """Get all registered Sparks."""
        return list(self._sparks.values())

    def list_names(self) -> List[str]:
        """Get names of all registered Sparks."""
        return list(self._sparks.keys())


# Global singleton
registry = SparkRegistry()
