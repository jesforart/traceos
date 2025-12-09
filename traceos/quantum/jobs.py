"""
Quantum Job Persistence

Stores and retrieves QuantumJobResult objects.

@provenance traceos_quantum_v1
@organ kernel
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from .schemas import QuantumJobResult

logger = logging.getLogger(__name__)


class QuantumJobStore:
    """
    File-based store for quantum jobs.
    Location: ./data/quantum_jobs/{job_id}.json
    """

    def __init__(self, base_dir: str = "./data/quantum_jobs"):
        self.path = Path(base_dir)
        self.path.mkdir(parents=True, exist_ok=True)

    def save(self, result: QuantumJobResult) -> None:
        """Save quantum job result to disk."""
        filepath = self.path / f"{result.job_id}.json"
        with open(filepath, 'w') as f:
            json.dump(result.model_dump(), f, default=str, indent=2)
        logger.debug(f"Saved quantum job: {result.job_id}")

    def load(self, job_id: str) -> Optional[QuantumJobResult]:
        """Load quantum job result by ID."""
        filepath = self.path / f"{job_id}.json"
        if not filepath.exists():
            return None

        with open(filepath, 'r') as f:
            data = json.load(f)
        return QuantumJobResult(**data)

    def list_job_ids(self) -> List[str]:
        """List all quantum job IDs."""
        return [p.stem for p in self.path.glob("*.json") if p.is_file()]
