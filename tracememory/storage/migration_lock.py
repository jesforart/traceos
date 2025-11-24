"""
Migration Lock - Multi-process safe migration locking

HARDENING v2.6 - Task 1: Multi-Process Migration Locking

Problem: Threading.Lock() only protects single-process. Multiple FastAPI workers
or agent instances could run migrations simultaneously, corrupting the database.

Solution: File-based interprocess lock using portalocker.
"""

import portalocker
from pathlib import Path
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)


class MigrationLock:
    """
    File-based interprocess lock for database migrations.

    Ensures only ONE process runs migrations at a time across:
    - Multiple FastAPI workers (gunicorn/uvicorn)
    - Multiple agent instances (Agent Zero + TraceOS)
    - Concurrent application processes

    Usage:
        with MigrationLock(db_path):
            # Run migration - guaranteed exclusive access
            migrate_to_v2_5(storage)
    """

    def __init__(self, db_path: str):
        """
        Create migration lock for a database file.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.lock_file = self.db_path.parent / f".{self.db_path.name}.migration.lock"
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock_handle: Optional[int] = None

    def __enter__(self):
        """Acquire exclusive lock (blocks until available)"""
        self._lock_handle = open(self.lock_file, 'w')

        logger.info(f"🔒 Acquiring migration lock: {self.lock_file}")
        portalocker.lock(self._lock_handle, portalocker.LOCK_EX)
        logger.info(f"✓ Migration lock acquired")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock"""
        if self._lock_handle:
            portalocker.unlock(self._lock_handle)
            self._lock_handle.close()
            logger.info(f"🔓 Migration lock released")
        return False

    def try_acquire(self, timeout: float = 5.0) -> bool:
        """
        Try to acquire lock with timeout.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if acquired, False if timeout
        """
        self._lock_handle = open(self.lock_file, 'w')

        try:
            # Try non-blocking first
            portalocker.lock(self._lock_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
            logger.info(f"✓ Migration lock acquired immediately")
            return True
        except portalocker.LockException:
            # Lock held by another process - wait with timeout
            logger.info(f"⏳ Migration lock held by another process, waiting up to {timeout}s...")
            start = time.time()
            while time.time() - start < timeout:
                try:
                    portalocker.lock(self._lock_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
                    elapsed = time.time() - start
                    logger.info(f"✓ Migration lock acquired after {elapsed:.2f}s")
                    return True
                except portalocker.LockException:
                    time.sleep(0.1)

            # Timeout
            elapsed = time.time() - start
            logger.warning(f"⏱️ Migration lock timeout after {elapsed:.2f}s")
            self._lock_handle.close()
            self._lock_handle = None
            return False

    def release(self):
        """Explicitly release the lock (called automatically on __exit__)"""
        if self._lock_handle:
            portalocker.unlock(self._lock_handle)
            self._lock_handle.close()
            self._lock_handle = None
            logger.info(f"🔓 Migration lock released explicitly")
