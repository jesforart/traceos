"""
Protocol Persistence Layer

JSON-based storage for intents, derivations, evaluations, and codifications.
Ensures TraceOS never loses provenance, even without database integration.

@provenance traceos_protocol_v1
@organ kernel
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, TypeVar, Type
from datetime import datetime

from .schemas import Intent, DeriveOutput, EvaluateOutput, CodifyOutput

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ProtocolStorage:
    """
    File-based storage for protocol data.

    Structure:
        data/protocol/
        ├── intents/{intent_id}.json
        ├── derivations/{derive_id}.json
        ├── evaluations/{derive_id}.json
        └── codifications/{derive_id}.json
    """

    def __init__(self, base_path: str = "/home/jesmosis/data/protocol"):
        """
        Initialize protocol storage.

        Args:
            base_path: Root directory for protocol data
        """
        self.base_path = Path(base_path)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        (self.base_path / "intents").mkdir(parents=True, exist_ok=True)
        (self.base_path / "derivations").mkdir(parents=True, exist_ok=True)
        (self.base_path / "evaluations").mkdir(parents=True, exist_ok=True)
        (self.base_path / "codifications").mkdir(parents=True, exist_ok=True)
        logger.info(f"Protocol storage initialized at: {self.base_path}")

    def save_intent(self, intent: Intent) -> None:
        """Save intent to disk."""
        path = self.base_path / "intents" / f"{intent.intent_id}.json"
        with open(path, 'w') as f:
            json.dump(intent.model_dump(), f, indent=2, default=str)
        logger.info(f"Saved intent: {intent.intent_id}")

    def load_intent(self, intent_id: str) -> Optional[Intent]:
        """Load intent from disk."""
        path = self.base_path / "intents" / f"{intent_id}.json"
        if not path.exists():
            return None

        with open(path, 'r') as f:
            data = json.load(f)
        return Intent(**data)

    def list_intents(self, tags: Optional[List[str]] = None) -> List[Intent]:
        """
        List all intents, optionally filtered by tags.

        Args:
            tags: Optional tag filter

        Returns:
            List of matching intents
        """
        intents_dir = self.base_path / "intents"
        intents = []

        for path in intents_dir.glob("*.json"):
            with open(path, 'r') as f:
                data = json.load(f)
            intent = Intent(**data)

            # Filter by tags if provided
            if tags is None or any(tag in intent.tags for tag in tags):
                intents.append(intent)

        return intents

    def save_derivation(self, derivation: DeriveOutput) -> None:
        """Save derivation output to disk."""
        path = self.base_path / "derivations" / f"{derivation.derive_id}.json"
        with open(path, 'w') as f:
            json.dump(derivation.model_dump(), f, indent=2, default=str)
        logger.info(f"Saved derivation: {derivation.derive_id}")

    def load_derivation(self, derive_id: str) -> Optional[DeriveOutput]:
        """Load derivation from disk."""
        path = self.base_path / "derivations" / f"{derive_id}.json"
        if not path.exists():
            return None

        with open(path, 'r') as f:
            data = json.load(f)
        return DeriveOutput(**data)

    def load_latest_derivation(self, intent_id: str) -> Optional[DeriveOutput]:
        """
        Load the most recent derivation for an intent.

        Args:
            intent_id: Intent to find derivation for

        Returns:
            Most recent DeriveOutput or None
        """
        derivations_dir = self.base_path / "derivations"
        matching_derivations = []

        for path in derivations_dir.glob("*.json"):
            with open(path, 'r') as f:
                data = json.load(f)

            if data.get("intent_id") == intent_id:
                matching_derivations.append((path.stat().st_mtime, DeriveOutput(**data)))

        if not matching_derivations:
            return None

        # Return most recent
        matching_derivations.sort(key=lambda x: x[0], reverse=True)
        return matching_derivations[0][1]

    def save_evaluation(self, evaluation: EvaluateOutput) -> None:
        """Save evaluation output to disk."""
        path = self.base_path / "evaluations" / f"{evaluation.derive_id}.json"
        with open(path, 'w') as f:
            json.dump(evaluation.model_dump(), f, indent=2, default=str)
        logger.info(f"Saved evaluation for: {evaluation.derive_id}")

    def load_evaluation(self, derive_id: str) -> Optional[EvaluateOutput]:
        """Load evaluation from disk."""
        path = self.base_path / "evaluations" / f"{derive_id}.json"
        if not path.exists():
            return None

        with open(path, 'r') as f:
            data = json.load(f)
        return EvaluateOutput(**data)

    def save_codification(self, codification: CodifyOutput) -> None:
        """Save codification output to disk."""
        path = self.base_path / "codifications" / f"{codification.derive_id}.json"
        with open(path, 'w') as f:
            json.dump(codification.model_dump(), f, indent=2, default=str)
        logger.info(f"Saved codification for: {codification.derive_id}")

    def load_codification(self, derive_id: str) -> Optional[CodifyOutput]:
        """Load codification from disk."""
        path = self.base_path / "codifications" / f"{derive_id}.json"
        if not path.exists():
            return None

        with open(path, 'r') as f:
            data = json.load(f)
        return CodifyOutput(**data)
