"""
Session index for fast lookups.

Maintains a lightweight index of all sessions with metadata,
enabling O(1) session existence checks without scanning directories.

Storage: ~/.memagent/index.json
Format: {session_id: {memory_block_id, last_updated, size_bytes, ...}}
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import portalocker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SessionIndex:
    """
    Fast index for session lookups.

    Features:
    - O(1) session existence checks
    - File locking for concurrent access
    - Automatic index repair/recovery
    - Sorted listing by update time
    """

    def __init__(self, index_path: Path):
        """
        Initialize session index.

        Args:
            index_path: Path to index.json file
        """
        self.path = Path(index_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self._write({})
            logger.info(f"Created new session index: {self.path}")

    def _read(self) -> Dict:
        """
        Read index with shared lock.

        Returns:
            Dictionary of session_id -> metadata
        """
        try:
            with open(self.path, 'r') as f:
                portalocker.lock(f, portalocker.LOCK_SH)
                try:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
                finally:
                    portalocker.unlock(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Index read failed, returning empty: {e}")
            return {}

    def _write(self, data: Dict):
        """
        Write index with exclusive lock.

        Args:
            data: Dictionary to write
        """
        try:
            with open(self.path, 'w') as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                try:
                    json.dump(data, f, indent=2, sort_keys=True)
                finally:
                    portalocker.unlock(f)
        except Exception as e:
            logger.error(f"Index write failed: {e}")
            raise

    def add(self, session_id: str, metadata: Dict):
        """
        Add or update session in index.

        Args:
            session_id: Session identifier
            metadata: Session metadata (memory_block_id, last_updated, etc)
        """
        index = self._read()
        index[session_id] = {
            **metadata,
            "indexed_at": datetime.utcnow().isoformat()
        }
        self._write(index)
        logger.debug(f"Session indexed: {session_id}")

    def remove(self, session_id: str):
        """
        Remove session from index.

        Args:
            session_id: Session identifier
        """
        index = self._read()
        if session_id in index:
            del index[session_id]
            self._write(index)
            logger.debug(f"Session removed from index: {session_id}")

    def get(self, session_id: str) -> Optional[Dict]:
        """
        Get session metadata.

        Args:
            session_id: Session identifier

        Returns:
            Session metadata or None if not found
        """
        index = self._read()
        return index.get(session_id)

    def exists(self, session_id: str) -> bool:
        """
        Check if session exists in index.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists
        """
        index = self._read()
        return session_id in index

    def list(self, limit: int = 100) -> List[Dict]:
        """
        List all sessions (most recent first).

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session metadata dicts with session_id
        """
        index = self._read()
        sessions = [
            {"session_id": sid, **meta}
            for sid, meta in index.items()
        ]

        # Sort by last_updated (most recent first)
        sessions.sort(
            key=lambda x: x.get("last_updated", ""),
            reverse=True
        )

        return sessions[:limit]

    def count(self) -> int:
        """
        Count total sessions in index.

        Returns:
            Number of sessions
        """
        index = self._read()
        return len(index)

    def repair(self, valid_session_ids: List[str]):
        """
        Repair index by removing orphaned entries.

        Args:
            valid_session_ids: List of session IDs that actually exist on disk
        """
        index = self._read()
        original_count = len(index)

        # Keep only sessions that exist
        repaired = {
            sid: meta
            for sid, meta in index.items()
            if sid in valid_session_ids
        }

        if len(repaired) < original_count:
            self._write(repaired)
            removed = original_count - len(repaired)
            logger.warning(f"Index repaired: removed {removed} orphaned entries")
