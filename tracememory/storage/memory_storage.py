"""
SQLite-based storage for memory blocks with WAL mode and checksums.

UPGRADED: November 2025 - Production hardening
- SQLite database with WAL (Write-Ahead Logging) mode
- SHA-256 checksums on every save
- Atomic UPSERT operations for crash safety
- Automatic migration from legacy JSON files
- Concurrent reads during writes
- Per-session storage with centralized database

Previous architecture (JSON files):
- File locking for concurrent writes
- Manual backup management
- Per-session JSON files

New architecture (SQLite + WAL):
- Automatic crash recovery
- Checksum validation on load
- Schema versioning for future migrations
- Better performance for write-heavy workloads

Directory structure:
~/.memagent/
├── traceos_memory.db          (NEW: centralized SQLite database)
├── traceos_memory.db-wal      (NEW: WAL file)
├── traceos_memory.db-shm      (NEW: shared memory file)
├── sessions/                   (LEGACY: migrated automatically)
│   ├── {session_id}/
│   │   ├── memory.json        (migrated to SQLite)
│   │   ├── assets/
│   │   │   ├── latest.svg
├── cache/
└── index.json
"""

import orjson
import shutil
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
import portalocker
import logging
from datetime import datetime

from models.memory import MemoryBlock, AssetState
from storage.index import SessionIndex
from config import settings

logger = logging.getLogger(__name__)


# SQLite Configuration
class StorageCorruptionError(Exception):
    """Raised when stored data fails checksum validation"""
    pass


# SQLite Schema (multi-session design)
SCHEMA = '''
CREATE TABLE IF NOT EXISTS memory_blocks (
  session_id   TEXT PRIMARY KEY,
  updated_at   TEXT NOT NULL,
  payload      BLOB NOT NULL,
  checksum     TEXT NOT NULL,
  schema_ver   INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_updated_at ON memory_blocks(updated_at);
'''


def compute_checksum(payload_bytes: bytes) -> str:
    """
    Compute SHA-256 checksum of payload.

    Args:
        payload_bytes: Raw bytes to checksum

    Returns:
        Hexadecimal string (64 characters)
    """
    return hashlib.sha256(payload_bytes).hexdigest()


def get_db_path(base_path: Path) -> Path:
    """
    Get path to centralized SQLite database.

    Args:
        base_path: Storage directory

    Returns:
        Path to traceos_memory.db
    """
    return base_path / "traceos_memory.db"


def get_connection(db_path: Path) -> sqlite3.Connection:
    """
    Create SQLite connection with WAL mode enabled.

    WAL (Write-Ahead Logging) provides:
    - Crash safety (no corruption on power loss)
    - Concurrent reads during writes
    - Better performance for write-heavy workloads

    Args:
        db_path: Path to database file

    Returns:
        Configured SQLite connection
    """
    conn = sqlite3.Connection(
        str(db_path),
        isolation_level=None,  # Autocommit mode
        check_same_thread=False  # Allow multi-threaded access
    )

    # Enable WAL mode
    conn.execute("PRAGMA journal_mode=WAL;")

    # Synchronous NORMAL for performance
    # (FULL is slower but safer, NORMAL is good balance)
    conn.execute("PRAGMA synchronous=NORMAL;")

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON;")

    # Log confirmation (only once)
    journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    if journal_mode == "wal":
        logger.debug(f"SQLite WAL mode enabled: {db_path.name}")
    else:
        logger.warning(f"SQLite WAL mode not enabled (got {journal_mode})")

    return conn


def initialize_database(db_path: Path):
    """
    Create database schema if not exists.

    Args:
        db_path: Path to database file
    """
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        logger.debug("Database schema initialized")
    finally:
        conn.close()


class MemoryStorage:
    """
    SQLite-based storage for memory blocks with WAL mode and checksums.

    Features (UPGRADED November 2025):
    - SQLite database with WAL mode for crash safety
    - SHA-256 checksums on every save
    - Atomic UPSERT operations
    - Concurrent reads during writes
    - Automatic migration from legacy JSON files
    - Session-based storage in centralized database
    - Asset management (still file-based)
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize memory storage with SQLite database.

        Args:
            base_path: Storage directory (defaults to settings.STORAGE_PATH)
        """
        self.base = Path(base_path or settings.STORAGE_PATH).expanduser()
        self.base.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database
        self.db_path = get_db_path(self.base)
        initialize_database(self.db_path)

        # Index still used for compatibility (will be updated to use SQLite)
        self.index = SessionIndex(self.base / "index.json")

        # Run automatic migration from legacy JSON files
        self._migrate_legacy_json_sessions()

        logger.info(f"MemoryStorage initialized (SQLite + WAL): {self.base}")

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
        Save memory block to SQLite database with atomic UPSERT.

        Process (UPGRADED to SQLite):
        1. Update timestamp
        2. Serialize to JSON bytes
        3. Compute SHA-256 checksum
        4. Validate size
        5. Atomic UPSERT to database (WAL mode = crash safe)
        6. Update index

        Args:
            block: MemoryBlock to save

        Returns:
            Path to database file (for compatibility)

        Raises:
            ValueError: If block is too large
            sqlite3.Error: If database write fails
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

        # Compute SHA-256 checksum of payload
        payload_checksum = compute_checksum(block_bytes)

        # Current timestamp
        timestamp = block.last_updated.isoformat()

        # Atomic UPSERT to SQLite (WAL mode ensures crash safety)
        conn = get_connection(self.db_path)
        try:
            conn.execute(
                '''
                INSERT INTO memory_blocks (session_id, updated_at, payload, checksum, schema_ver)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(session_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    payload    = excluded.payload,
                    checksum   = excluded.checksum,
                    schema_ver = excluded.schema_ver
                ''',
                (block.session_id, timestamp, block_bytes, payload_checksum)
            )

            # Update index
            self.index.add(block.session_id, {
                "memory_block_id": block.memory_block_id,
                "last_updated": timestamp,
                "size_bytes": size_bytes
            })

            logger.info(
                f"Memory block saved to SQLite: {block.session_id} "
                f"({size_bytes} bytes, checksum: {payload_checksum[:16]}...)"
            )

        finally:
            conn.close()

        return self.db_path  # Return db path for compatibility

    def load_memory_block(self, session_id: str) -> Optional[MemoryBlock]:
        """
        Load memory block from SQLite database with checksum validation.

        Process (UPGRADED to SQLite):
        1. Query database for session
        2. Validate SHA-256 checksum
        3. Parse JSON payload
        4. Return MemoryBlock

        Args:
            session_id: Session identifier

        Returns:
            MemoryBlock or None if not found

        Raises:
            StorageCorruptionError: If checksum validation fails
            orjson.JSONDecodeError: If JSON is malformed
        """
        conn = get_connection(self.db_path)
        try:
            # Load row for session
            result = conn.execute(
                "SELECT payload, checksum FROM memory_blocks WHERE session_id = ?",
                (session_id,)
            ).fetchone()

            if result is None:
                logger.debug(f"Memory block not found in SQLite: {session_id}")
                return None

            payload_bytes, stored_checksum = result

            # Validate SHA-256 checksum
            computed_checksum = compute_checksum(payload_bytes)
            if computed_checksum != stored_checksum:
                logger.error(
                    f"Checksum mismatch! Session: {session_id}, "
                    f"Stored: {stored_checksum[:16]}..., "
                    f"Computed: {computed_checksum[:16]}..."
                )
                raise StorageCorruptionError(
                    f"Memory block corrupted (checksum mismatch): {session_id}"
                )

            # Decode payload
            data = orjson.loads(payload_bytes)
            block = MemoryBlock(**data)

            # Additional validation: MemoryBlock's internal checksum
            if not block.validate_checksum():
                logger.warning(
                    f"MemoryBlock internal checksum mismatch for {session_id} "
                    f"(SQLite checksum OK, but block.checksum field doesn't match)"
                )

            logger.debug(f"Memory block loaded from SQLite: {session_id}")
            return block

        except orjson.JSONDecodeError as e:
            logger.error(f"Failed to parse memory block {session_id}: {e}")
            raise
        except StorageCorruptionError:
            raise
        except Exception as e:
            logger.error(f"Failed to load memory block {session_id}: {e}")
            raise
        finally:
            conn.close()

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
        Delete session from SQLite database and remove directory.

        Args:
            session_id: Session identifier
        """
        # Delete from SQLite
        conn = get_connection(self.db_path)
        try:
            conn.execute("DELETE FROM memory_blocks WHERE session_id = ?", (session_id,))
            logger.debug(f"Deleted session from SQLite: {session_id}")
        finally:
            conn.close()

        # Delete session directory (assets, etc.)
        session_dir = self.session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)

        # Remove from index
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
        Check if session exists in SQLite database.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists in SQLite
        """
        conn = get_connection(self.db_path)
        try:
            result = conn.execute(
                "SELECT COUNT(*) FROM memory_blocks WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            return result[0] > 0
        finally:
            conn.close()

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

    def _migrate_legacy_json_sessions(self) -> int:
        """
        Automatically migrate legacy JSON files to SQLite database.

        Scans sessions directory for memory.json files and migrates them
        to the centralized SQLite database. Renames migrated JSON files
        to memory.json.migrated to prevent re-migration.

        Returns:
            Number of sessions migrated
        """
        sessions_dir = self.base / "sessions"
        if not sessions_dir.exists():
            logger.debug("No legacy sessions directory found, skipping migration")
            return 0

        migrated_count = 0

        # Find all session directories with memory.json files
        for session_dir in sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue

            memory_json = session_dir / "memory.json"
            if not memory_json.exists():
                continue

            session_id = session_dir.name

            # Check if already in SQLite
            conn = get_connection(self.db_path)
            try:
                result = conn.execute(
                    "SELECT COUNT(*) FROM memory_blocks WHERE session_id = ?",
                    (session_id,)
                ).fetchone()

                if result[0] > 0:
                    logger.debug(f"Session {session_id} already in SQLite, skipping")
                    continue

                # Load legacy JSON
                try:
                    data = orjson.loads(memory_json.read_bytes())
                    block = MemoryBlock(**data)

                    logger.info(f"Migrating session {session_id} from JSON to SQLite")

                    # Save to SQLite (using existing save_memory_block method)
                    self.save_memory_block(block)

                    # Rename JSON file to prevent re-migration
                    migrated_path = memory_json.with_suffix('.json.migrated')
                    memory_json.rename(migrated_path)

                    migrated_count += 1
                    logger.info(f"Migrated session {session_id} successfully")

                except Exception as e:
                    logger.error(f"Failed to migrate session {session_id}: {e}")
                    continue

            finally:
                conn.close()

        if migrated_count > 0:
            logger.info(f"Migration complete: {migrated_count} sessions migrated to SQLite")
        else:
            logger.debug("No legacy sessions found to migrate")

        return migrated_count

    def _cleanup_backups(self, backup_dir: Path, keep: int = 5):
        """
        Keep only the N most recent backups (DEPRECATED - no longer used with SQLite).

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
        Repair index by scanning SQLite database.

        Rebuilds index from sessions actually stored in the database.
        """
        conn = get_connection(self.db_path)
        try:
            # Get all session IDs from SQLite
            result = conn.execute(
                "SELECT session_id FROM memory_blocks"
            ).fetchall()

            valid_session_ids = [row[0] for row in result]

            # Repair index
            self.index.repair(valid_session_ids)

            logger.info(f"Index repaired from SQLite: {len(valid_session_ids)} sessions found")

        finally:
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """
        Get SQLite connection to the memory database.

        This is used by v2.5 migrations and other modules that need
        direct database access.

        Returns:
            SQLite connection with WAL mode enabled
        """
        return get_connection(self.db_path)

    # ==============================================================================
    # COGNITIVE KERNEL v2.5 - STORAGE METHODS (WITH RED TEAM FIXES)
    # ==============================================================================

    def run_cognitive_kernel_migration(self):
        """
        Run Cognitive Kernel v2.5 migration with RED TEAM fixes.

        This is idempotent and safe to run multiple times.

        HARDENING v2.6 - Task 1: Uses interprocess lock to prevent
        concurrent migrations from multiple workers/agents.
        """
        from tracememory.storage.migrations.v2_5_cognitive_kernel import migrate_to_v2_5
        from tracememory.storage.migration_lock import MigrationLock

        # HARDENING: Use interprocess lock for migration safety
        with MigrationLock(str(self.db_path)):
            migrate_to_v2_5(self)

    # ---- Cognitive Memory Blocks ----

    def save_cognitive_memory_block(self, block) -> str:
        """
        Save a Cognitive Kernel MemoryBlock to SQLite.

        RED TEAM FIX #3: Enforces uniqueness via (session_id, artifact_id) constraint.

        Args:
            block: CognitiveMemoryBlock instance

        Returns:
            Block ID
        """
        conn = get_connection(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO cognitive_memory_blocks
                (id, session_id, artifact_id, created_at, updated_at, ld_context,
                 derived_from, intent_profile_id, style_dna_id, tags, notes, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                block.id, block.session_id, block.artifact_id,
                block.created_at.isoformat(), block.updated_at.isoformat(),
                orjson.dumps(block.ld_context).decode(),
                block.derived_from, block.intent_profile_id, block.style_dna_id,
                orjson.dumps(block.tags).decode(), block.notes,
                orjson.dumps(block.metadata).decode()
            ))
            conn.commit()
            logger.debug(f"Saved cognitive memory block: {block.id}")
        finally:
            conn.close()
        return block.id

    def get_cognitive_memory_block(self, block_id: str):
        """Retrieve a Cognitive Memory Block (read-only, no lock needed)"""
        from tracememory.models.memory import CognitiveMemoryBlock

        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM cognitive_memory_blocks WHERE id = ?", (block_id,)
            ).fetchone()

            if not row:
                return None

            return CognitiveMemoryBlock(
                id=row[0],
                session_id=row[1],
                artifact_id=row[2],
                created_at=datetime.fromisoformat(row[3]),
                updated_at=datetime.fromisoformat(row[4]),
                ld_context=orjson.loads(row[5]),
                derived_from=row[6],
                intent_profile_id=row[7],
                style_dna_id=row[8],
                tags=orjson.loads(row[9]),
                notes=row[10],
                metadata=orjson.loads(row[11])
            )
        finally:
            conn.close()

    def get_cognitive_memory_block_by_artifact(
        self,
        session_id: str,
        artifact_id: str
    ):
        """
        Retrieve Cognitive Memory Block by (session_id, artifact_id) composite key.

        RED TEAM FIX #3: Uses composite key for unambiguous retrieval.
        """
        from tracememory.models.memory import CognitiveMemoryBlock

        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM cognitive_memory_blocks WHERE session_id = ? AND artifact_id = ?",
                (session_id, artifact_id)
            ).fetchone()

            if not row:
                return None

            return CognitiveMemoryBlock(
                id=row[0],
                session_id=row[1],
                artifact_id=row[2],
                created_at=datetime.fromisoformat(row[3]),
                updated_at=datetime.fromisoformat(row[4]),
                ld_context=orjson.loads(row[5]),
                derived_from=row[6],
                intent_profile_id=row[7],
                style_dna_id=row[8],
                tags=orjson.loads(row[9]),
                notes=row[10],
                metadata=orjson.loads(row[11])
            )
        finally:
            conn.close()

    # ---- Style DNA ----

    def save_style_dna(self, style) -> str:
        """
        Save StyleDNA with vectors as BLOBs.

        RED TEAM FIX #4: Vectors validated before storage via Pydantic validators.
        """
        from tracememory.storage.migrations.v2_5_cognitive_kernel import vector_to_blob

        conn = get_connection(self.db_path)
        try:
            # Convert vectors to blobs (validation happens in vector_to_blob)
            stroke_blob = vector_to_blob(style.stroke_dna) if style.stroke_dna else None
            image_blob = vector_to_blob(style.image_dna) if style.image_dna else None
            temporal_blob = vector_to_blob(style.temporal_dna) if style.temporal_dna else None

            conn.execute("""
                INSERT OR REPLACE INTO style_dna
                (id, artifact_id, stroke_dna, image_dna, temporal_dna, created_at, l2_norm, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                style.id, style.artifact_id,
                stroke_blob, image_blob, temporal_blob,
                style.created_at.isoformat(), style.l2_norm, style.checksum
            ))
            conn.commit()
            logger.debug(f"Saved Style DNA: {style.id}")
        finally:
            conn.close()
        return style.id

    def get_style_dna(self, style_id: str):
        """
        Retrieve StyleDNA with vectors from BLOBs.

        RED TEAM FIX #4: Vectors validated after loading via blob_to_vector.
        HARDENING v2.6 - Task 4: Verifies checksum to detect corruption.
        """
        from tracememory.models.memory import StyleDNA
        from tracememory.storage.migrations.v2_5_cognitive_kernel import blob_to_vector
        from tracememory.storage.vector_utils import verify_style_dna_checksum

        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM style_dna WHERE id = ?", (style_id,)
            ).fetchone()

            if not row:
                return None

            # Load vectors
            stroke_dna = blob_to_vector(row[2]) if row[2] else None
            image_dna = blob_to_vector(row[3]) if row[3] else None
            temporal_dna = blob_to_vector(row[4]) if row[4] else None
            checksum = row[7]

            # HARDENING v2.6 - Task 4: Verify checksum if present
            if checksum and not verify_style_dna_checksum(stroke_dna, image_dna, temporal_dna, checksum):
                raise ValueError(
                    f"StyleDNA checksum mismatch for {style_id} - "
                    f"vector corruption detected! Expected checksum: {checksum}"
                )

            return StyleDNA(
                id=row[0],
                artifact_id=row[1],
                stroke_dna=stroke_dna,
                image_dna=image_dna,
                temporal_dna=temporal_dna,
                created_at=datetime.fromisoformat(row[5]),
                l2_norm=row[6],
                checksum=checksum
            )
        finally:
            conn.close()

    # ---- Intent Profiles ----

    def save_intent_profile(self, intent) -> str:
        """Save IntentProfile to SQLite"""
        conn = get_connection(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO intent_profiles
                (id, session_id, artifact_id, emotional_register, target_audience,
                 constraints, narrative_prompt, style_keywords, created_at, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                intent.id, intent.session_id, intent.artifact_id,
                orjson.dumps(intent.emotional_register).decode(), intent.target_audience,
                orjson.dumps(intent.constraints).decode(), intent.narrative_prompt,
                orjson.dumps(intent.style_keywords).decode(),
                intent.created_at.isoformat(), intent.source
            ))
            conn.commit()
            logger.debug(f"Saved Intent Profile: {intent.id}")
        finally:
            conn.close()
        return intent.id

    def get_intent_profile(self, intent_id: str):
        """Retrieve IntentProfile"""
        from tracememory.models.memory import IntentProfile

        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM intent_profiles WHERE id = ?", (intent_id,)
            ).fetchone()

            if not row:
                return None

            return IntentProfile(
                id=row[0],
                session_id=row[1],
                artifact_id=row[2],
                emotional_register=orjson.loads(row[3]),
                target_audience=row[4],
                constraints=orjson.loads(row[5]),
                narrative_prompt=row[6],
                style_keywords=orjson.loads(row[7]),
                created_at=datetime.fromisoformat(row[8]),
                source=row[9]
            )
        finally:
            conn.close()

    # ---- Telemetry Chunks ----

    def save_telemetry_chunk(self, chunk) -> str:
        """Save TelemetryChunk metadata"""
        conn = get_connection(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO telemetry_chunks
                (id, session_id, artifact_id, parquet_path, chunk_row_count,
                 total_session_rows, created_at, schema_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk.id, chunk.session_id, chunk.artifact_id,
                chunk.parquet_path, chunk.chunk_row_count, chunk.total_session_rows,
                chunk.created_at.isoformat(), chunk.schema_version
            ))
            conn.commit()
            logger.debug(f"Saved Telemetry Chunk: {chunk.id}")
        finally:
            conn.close()
        return chunk.id

    def get_telemetry_chunk(self, chunk_id: str):
        """Retrieve TelemetryChunk metadata"""
        from tracememory.models.memory import TelemetryChunk

        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM telemetry_chunks WHERE id = ?", (chunk_id,)
            ).fetchone()

            if not row:
                return None

            return TelemetryChunk(
                id=row[0],
                session_id=row[1],
                artifact_id=row[2],
                parquet_path=row[3],
                chunk_row_count=row[4],
                total_session_rows=row[5],
                created_at=datetime.fromisoformat(row[6]),
                schema_version=row[7]
            )
        finally:
            conn.close()
