"""
File-based storage for memory blocks with concurrent write protection.

Provides durable, transactional storage with:
- File locking for concurrent writes
- Automatic backups on save
- Checksum validation
- Size limits
- Asset management

Directory structure:
~/.memagent/
├── sessions/
│   ├── {session_id}/
│   │   ├── memory.json
│   │   ├── memory.json.lock
│   │   ├── assets/
│   │   │   ├── latest.svg
│   │   │   ├── 2025-10-27T03-11-02.svg
│   │   └── backups/
│   │       ├── memory.2025-10-27T03-11-02.json
├── cache/
└── index.json
"""

import orjson
import shutil
from pathlib import Path
from typing import Optional, List, Dict
import portalocker
import logging
from datetime import datetime

from models.memory import MemoryBlock, AssetState
from storage.index import SessionIndex
from config import settings

logger = logging.getLogger(__name__)


class MemoryStorage:
    """
    File-based storage for memory blocks with concurrent write protection.

    Features:
    - File locking for concurrent writes
    - Automatic backups (keeps last 5)
    - Checksum validation on load
    - Size limit enforcement
    - Index for fast lookups
    - Asset management
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize memory storage.

        Args:
            base_path: Storage directory (defaults to settings.STORAGE_PATH)
        """
        self.base = Path(base_path or settings.STORAGE_PATH).expanduser()
        self.base.mkdir(parents=True, exist_ok=True)

        self.index = SessionIndex(self.base / "index.json")

        logger.info(f"MemoryStorage initialized: {self.base}")

    def session_dir(self, session_id: str) -> Path:
        """
        Get session directory, create if needed.

        Args:
            session_id: Session identifier

        Returns:
            Path to session directory
        """
        p = self.base / "sessions" / session_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def save_memory_block(self, block: MemoryBlock) -> Path:
        """
        Save memory block to disk with locking and backup.

        Process:
        1. Compute checksum
        2. Validate size
        3. Acquire file lock
        4. Backup existing file
        5. Write new file atomically
        6. Update index
        7. Release lock

        Args:
            block: MemoryBlock to save

        Returns:
            Path to saved memory.json

        Raises:
            ValueError: If block is too large
            IOError: If write fails
        """
        # Update timestamp BEFORE computing checksum
        block.last_updated = datetime.utcnow()
        # Compute checksum after all fields are set
        block.checksum = block.compute_checksum()

        # Serialize and validate size
        block_data = block.dict()
        block_bytes = orjson.dumps(
            block_data,
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
        )
        size_bytes = len(block_bytes)

        if size_bytes > settings.MAX_MEMORY_BLOCK_SIZE:
            raise ValueError(
                f"Memory block too large: {size_bytes} bytes "
                f"(max {settings.MAX_MEMORY_BLOCK_SIZE})"
            )

        # Paths
        session_dir = self.session_dir(block.session_id)
        memory_path = session_dir / "memory.json"
        lock_path = session_dir / "memory.json.lock"
        backup_dir = session_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        # Acquire lock and write
        with open(lock_path, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)

            try:
                # Backup existing file
                if memory_path.exists():
                    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
                    backup_path = backup_dir / f"memory.{timestamp}.json"

                    try:
                        shutil.copy2(memory_path, backup_path)
                        logger.debug(f"Backed up memory block: {backup_path.name}")
                    except Exception as e:
                        logger.warning(f"Backup failed (continuing): {e}")

                    # Keep only last 5 backups
                    self._cleanup_backups(backup_dir, keep=5)

                # Write new file atomically (write to temp, then rename)
                temp_path = memory_path.with_suffix('.json.tmp')
                temp_path.write_bytes(block_bytes)
                temp_path.replace(memory_path)

                # Update index
                self.index.add(block.session_id, {
                    "memory_block_id": block.memory_block_id,
                    "last_updated": block.last_updated.isoformat(),
                    "size_bytes": size_bytes
                })

                logger.info(
                    f"Memory block saved: {block.session_id} "
                    f"({size_bytes} bytes, checksum: {block.checksum[:8]}...)"
                )

            finally:
                portalocker.unlock(lock_file)

        return memory_path

    def load_memory_block(self, session_id: str) -> Optional[MemoryBlock]:
        """
        Load memory block from disk with validation.

        Process:
        1. Read file
        2. Parse JSON
        3. Validate checksum
        4. Return MemoryBlock

        Args:
            session_id: Session identifier

        Returns:
            MemoryBlock or None if not found

        Raises:
            ValueError: If checksum validation fails
            orjson.JSONDecodeError: If JSON is malformed
        """
        memory_path = self.session_dir(session_id) / "memory.json"

        if not memory_path.exists():
            logger.debug(f"Memory block not found: {session_id}")
            return None

        try:
            data = orjson.loads(memory_path.read_bytes())
            block = MemoryBlock(**data)

            # Validate checksum
            if not block.validate_checksum():
                logger.error(f"Checksum validation failed for {session_id}")
                raise ValueError(
                    f"Memory block corrupted (checksum mismatch): {session_id}"
                )

            logger.debug(f"Memory block loaded: {session_id}")
            return block

        except orjson.JSONDecodeError as e:
            logger.error(f"Failed to parse memory block {session_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load memory block {session_id}: {e}")
            raise

    def save_asset(self, session_id: str, asset: AssetState) -> Path:
        """
        Save asset to disk.

        Stores:
        - Timestamped file: assets/2025-10-27T03-11-02.svg
        - Latest symlink: assets/latest.svg

        Args:
            session_id: Session identifier
            asset: Asset to save

        Returns:
            Path to saved asset file
        """
        assets_dir = self.session_dir(session_id) / "assets"
        assets_dir.mkdir(exist_ok=True)

        # Timestamped filename
        timestamp = asset.created_at.strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"{timestamp}.{asset.type.value}"
        path = assets_dir / filename
        path.write_text(asset.data)

        # Update "latest" symlink
        latest = assets_dir / f"latest.{asset.type.value}"
        if latest.exists() or latest.is_symlink():
            latest.unlink()

        # Create relative symlink
        latest.symlink_to(filename)

        logger.debug(f"Asset saved: {session_id}/{filename} ({asset.size_bytes} bytes)")

        return path

    def load_latest_asset(self, session_id: str) -> Optional[AssetState]:
        """
        Load most recent asset from memory block.

        Args:
            session_id: Session identifier

        Returns:
            AssetState or None if no asset exists
        """
        memory = self.load_memory_block(session_id)
        if memory and memory.last_asset:
            return memory.last_asset
        return None

    def delete_session(self, session_id: str):
        """
        Delete entire session directory.

        Args:
            session_id: Session identifier
        """
        session_dir = self.session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
            self.index.remove(session_id)
            logger.info(f"Session deleted: {session_id}")

    def list_sessions(self, limit: int = 100) -> List[Dict]:
        """
        List all sessions from index.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session metadata dicts
        """
        return self.index.list(limit)

    def session_exists(self, session_id: str) -> bool:
        """
        Check if session exists.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists in index
        """
        return self.index.exists(session_id)

    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics.

        Returns:
            Dict with storage metrics
        """
        sessions_dir = self.base / "sessions"
        if not sessions_dir.exists():
            return {
                "total_sessions": 0,
                "total_size_bytes": 0,
                "storage_path": str(self.base)
            }

        total_size = sum(
            f.stat().st_size
            for f in sessions_dir.rglob('*')
            if f.is_file()
        )

        return {
            "total_sessions": self.index.count(),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(self.base)
        }

    def _cleanup_backups(self, backup_dir: Path, keep: int = 5):
        """
        Keep only the N most recent backups.

        Args:
            backup_dir: Directory containing backups
            keep: Number of backups to keep
        """
        backups = sorted(backup_dir.glob("memory.*.json"), key=lambda p: p.stat().st_mtime)

        # Delete old backups
        if len(backups) > keep:
            for old_backup in backups[:-keep]:
                try:
                    old_backup.unlink()
                    logger.debug(f"Deleted old backup: {old_backup.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete backup {old_backup.name}: {e}")

    def repair_index(self):
        """
        Repair index by scanning actual sessions on disk.

        Useful after manual file operations or corruption.
        """
        sessions_dir = self.base / "sessions"
        if not sessions_dir.exists():
            logger.warning("No sessions directory found")
            return

        # Find all session directories
        session_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
        valid_session_ids = [d.name for d in session_dirs]

        # Repair index
        self.index.repair(valid_session_ids)

        logger.info(f"Index repaired: {len(valid_session_ids)} sessions found")
