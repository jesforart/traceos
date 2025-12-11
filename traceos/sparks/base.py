"""
TraceOS Spark Base Class

Abstract base class for all Spark organs.
Each Spark implements specialized cognitive functions.
"""

from abc import ABC, abstractmethod
from typing import Any

from traceos.sparks.schemas import SparkMetadata, SparkState, SparkResponse
from traceos.protocol.schemas import DeriveOutput


class SparkBase(ABC):
    """
    Abstract base class for Spark organs.

    Each Spark organ:
        - Maintains persistent state
        - Evaluates derivations from its perspective
        - Contributes to collective decision-making
    """

    def __init__(self, metadata: SparkMetadata) -> None:
        self._metadata = metadata
        self._state = SparkState(spark_id=metadata.id)

    @property
    def metadata(self) -> SparkMetadata:
        """Get Spark metadata."""
        return self._metadata

    @property
    def state(self) -> SparkState:
        """Get current Spark state."""
        return self._state

    @abstractmethod
    async def evaluate(self, derivation: DeriveOutput) -> SparkResponse:
        """
        Evaluate a derivation from this Spark's perspective.

        Args:
            derivation: The output to evaluate.

        Returns:
            SparkResponse with approval status and reasoning.
        """
        raise NotImplementedError(
            "Proprietary Neural/Quantum IP - See Patent US 63/926,510"
        )

    @abstractmethod
    async def update_state(self, data: dict[str, Any]) -> None:
        """
        Update Spark state based on new information.

        Args:
            data: State update data.
        """
        raise NotImplementedError(
            "Proprietary Neural/Quantum IP - See Patent US 63/926,510"
        )

    async def reset(self) -> None:
        """Reset Spark to initial state."""
        self._state = SparkState(spark_id=self._metadata.id)
