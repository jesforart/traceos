"""
Spark Base Class

Abstract base for all TraceOS cognitive organs.

@provenance traceos_sparks_v1
@organ kernel
"""

from abc import ABC, abstractmethod
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from .schemas import SparkMetadata, SparkState
from traceos.protocol.schemas import DeriveOutput, SparkReview

logger = logging.getLogger(__name__)


class SparkBase(ABC):
    """
    Base class for all Spark organs.

    Sparks are stateful cognitive organs that:
    - Evaluate derivations
    - Maintain internal state
    - Persist memory between sessions
    - Evolve over time
    """

    def __init__(self):
        self.metadata = self._define_metadata()
        self.state = self._load_state() or SparkState()
        logger.info(f"Initialized {self.metadata.name} Spark (v{self.metadata.version})")

    @abstractmethod
    def _define_metadata(self) -> SparkMetadata:
        """Define this Spark's identity and purpose."""
        pass

    @abstractmethod
    def evaluate(self, derivation: DeriveOutput) -> SparkReview:
        """
        Analyze a derivation and return a review.

        Args:
            derivation: The derivation to evaluate

        Returns:
            SparkReview with status, score, and comments
        """
        pass

    def update_state(self, **kwargs):
        """
        Update Spark state.

        Args:
            **kwargs: State fields to update (activation, fatigue, mood, memory)
        """
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)

        self.state.last_updated = datetime.utcnow()
        self._persist_state()

    def _persist_state(self):
        """Save state to disk (data/sparks/{name}.json)."""
        path = Path(f"/home/jesmosis/data/sparks/{self.metadata.name.lower()}.json")
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(self.state.model_dump(), f, indent=2, default=str)

        logger.debug(f"Persisted {self.metadata.name} state to {path}")

    def _load_state(self) -> Optional[SparkState]:
        """Load state from disk if it exists."""
        path = Path(f"/home/jesmosis/data/sparks/{self.metadata.name.lower()}.json")

        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                logger.debug(f"Loaded {self.metadata.name} state from {path}")
                return SparkState(**data)

        return None
