"""
TraceOS Spark Registry

Singleton registry for managing all Spark organs.
Provides centralized access to the cognitive ensemble.
"""

from typing import Optional
from uuid import UUID

from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata


class SparkRegistry:
    """
    Registry for all Spark organs.

    The registry provides:
        - Centralized Spark access
        - Lifecycle management
        - Collective evaluation orchestration
    """

    _instance: Optional["SparkRegistry"] = None

    def __new__(cls) -> "SparkRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sparks = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._sparks: dict[str, SparkBase] = {}
            self._initialized = True

    def register(self, name: str, spark: SparkBase) -> None:
        """
        Register a Spark organ.

        Args:
            name: Unique identifier for the Spark.
            spark: SparkBase instance to register.
        """
        if name in self._sparks:
            raise ValueError(f"Spark '{name}' already registered")
        self._sparks[name] = spark

    def get(self, name: str) -> Optional[SparkBase]:
        """
        Get a registered Spark by name.

        Args:
            name: Spark identifier.

        Returns:
            SparkBase instance or None if not found.
        """
        return self._sparks.get(name)

    def get_by_id(self, spark_id: UUID) -> Optional[SparkBase]:
        """
        Get a registered Spark by UUID.

        Args:
            spark_id: Spark UUID.

        Returns:
            SparkBase instance or None if not found.
        """
        for spark in self._sparks.values():
            if spark.metadata.id == spark_id:
                return spark
        return None

    def all_sparks(self) -> list[SparkBase]:
        """Get all registered Sparks."""
        return list(self._sparks.values())

    def spark_names(self) -> list[str]:
        """Get names of all registered Sparks."""
        return list(self._sparks.keys())

    def unregister(self, name: str) -> bool:
        """
        Unregister a Spark organ.

        Args:
            name: Spark identifier.

        Returns:
            True if Spark was removed, False if not found.
        """
        if name in self._sparks:
            del self._sparks[name]
            return True
        return False

    def clear(self) -> None:
        """Remove all registered Sparks."""
        self._sparks.clear()
