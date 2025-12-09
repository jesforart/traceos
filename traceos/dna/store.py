"""
Creative DNA Store

File-based storage for StyleSignatures and DNA lineage.

Layout:
- ./data/dna/signatures/{signature_id}.json
- ./data/dna/lineage.json
- ./data/dna/profile.json

@provenance traceos_dna_v1
@organ kernel
"""

import json
import logging
from pathlib import Path
from typing import Optional, List

from .schemas import StyleSignature, DNALineageNode, DNAProfileSummary

logger = logging.getLogger(__name__)


class DNAStore:
    """
    Manages storage of creative DNA signatures and lineage.

    Provides persistence layer for TraceOS identity memory.
    """

    def __init__(self, base_dir: str = "./data/dna"):
        self.base_path = Path(base_dir)
        self.signatures_path = self.base_path / "signatures"
        self.signatures_path.mkdir(parents=True, exist_ok=True)

        self.lineage_file = self.base_path / "lineage.json"
        self.profile_file = self.base_path / "profile.json"

        logger.debug(f"DNAStore initialized at {self.base_path}")

    def save_signature(self, signature: StyleSignature) -> None:
        """Save a StyleSignature to disk."""
        path = self.signatures_path / f"{signature.signature_id}.json"
        with open(path, "w") as f:
            json.dump(signature.model_dump(), f, default=str, indent=2)
        logger.info(f"Saved DNA signature: {signature.signature_id}")

    def load_signature(self, signature_id: str) -> Optional[StyleSignature]:
        """Load a StyleSignature by ID."""
        path = self.signatures_path / f"{signature_id}.json"
        if not path.exists():
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return StyleSignature(**data)

    def list_signature_ids(self) -> List[str]:
        """List all saved signature IDs."""
        return [
            p.stem for p in self.signatures_path.glob("*.json")
            if p.is_file()
        ]

    def get_latest_signature(self) -> Optional[StyleSignature]:
        """Return the most recently created signature, if any."""
        ids = self.list_signature_ids()
        if not ids:
            return None

        # Sort by filename (timestamp encoding in signature_id)
        latest_id = sorted(ids)[-1]
        return self.load_signature(latest_id)

    def save_lineage(self, nodes: List[DNALineageNode]) -> None:
        """Persist full lineage list."""
        with open(self.lineage_file, "w") as f:
            json.dump(
                [n.model_dump() for n in nodes],
                f,
                default=str,
                indent=2
            )
        logger.debug(f"Saved DNA lineage ({len(nodes)} nodes)")

    def load_lineage(self) -> List[DNALineageNode]:
        """Load lineage list from disk."""
        if not self.lineage_file.exists():
            return []

        with open(self.lineage_file, "r") as f:
            data = json.load(f)
        return [DNALineageNode(**n) for n in data]

    def save_profile(self, profile: DNAProfileSummary) -> None:
        """Persist DNA profile summary."""
        with open(self.profile_file, "w") as f:
            json.dump(profile.model_dump(), f, default=str, indent=2)

    def load_profile(self) -> DNAProfileSummary:
        """Load DNA profile summary, or create default."""
        if not self.profile_file.exists():
            return DNAProfileSummary()

        with open(self.profile_file, "r") as f:
            data = json.load(f)
        return DNAProfileSummary(**data)
