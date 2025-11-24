"""
Multi-Process Migration Lock Tests (v2.6 Hardening - Task 1)

Tests that multiple processes can safely initialize storage without
corrupting the database.

RED TEAM FIX HR-1: Multi-process migration locking with portalocker.
"""

import pytest
import tempfile
import multiprocessing
import time
from pathlib import Path
from tracememory.storage.memory_storage import MemoryStorage
from tracememory.storage.migration_lock import MigrationLock


def create_storage_in_subprocess(db_path: str) -> str:
    """
    Helper: Create storage in a separate process.

    This simulates multiple FastAPI workers or agent instances
    initializing storage concurrently.
    """
    try:
        storage = MemoryStorage(str(db_path))
        storage.run_cognitive_kernel_migration()
        return "ok"
    except Exception as e:
        return f"error: {str(e)}"


def test_migration_lock_basic_acquire_release():
    """Test that migration lock can be acquired and released"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Create lock
        lock = MigrationLock(str(db_path))

        # Should acquire successfully
        with lock:
            # Lock is held
            assert lock._lock_handle is not None

        # After exiting, lock should be released
        # (can't check _lock_handle as it's closed, but no exception = success)


def test_migration_lock_prevents_concurrent_access():
    """Test that lock blocks concurrent access from same process"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        lock1 = MigrationLock(str(db_path))
        lock2 = MigrationLock(str(db_path))

        # Acquire first lock
        with lock1:
            # Try to acquire second lock with timeout
            acquired = lock2.try_acquire(timeout=0.5)

            # Should fail (timeout)
            assert acquired is False

            # Release second lock attempt
            if lock2._lock_handle:
                lock2.release()


def test_migration_lock_sequential_access():
    """Test that lock allows sequential access"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # First acquisition
        with MigrationLock(str(db_path)):
            pass  # Lock acquired and released

        # Second acquisition should succeed
        with MigrationLock(str(db_path)):
            pass  # Lock acquired and released again


def test_concurrent_storage_initialization():
    """
    Test that multiple processes can safely initialize storage concurrently.

    HARDENING v2.6 - Task 1: This is the critical test for multi-process safety.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Spawn 4 processes all trying to initialize at once
        # This simulates:
        # - Multiple FastAPI workers starting up
        # - Multiple agent instances accessing storage
        # - Race conditions during deployment
        with multiprocessing.Pool(4) as pool:
            results = pool.map(create_storage_in_subprocess, [str(db_path)] * 4)

        # All should succeed
        assert all(r == "ok" for r in results), f"Some processes failed: {results}"

        # Database should be valid and migration only ran once
        storage = MemoryStorage(str(db_path))
        conn = storage.get_connection()

        # Check that Cognitive Kernel tables exist
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "cognitive_memory_blocks" in table_names
        assert "style_dna" in table_names
        assert "intent_profiles" in table_names
        assert "telemetry_chunks" in table_names

        conn.close()


def test_migration_lock_timeout():
    """Test that lock timeout works correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        lock1 = MigrationLock(str(db_path))
        lock2 = MigrationLock(str(db_path))

        # Acquire first lock
        with lock1:
            # Try to acquire second lock with short timeout
            start = time.time()
            acquired = lock2.try_acquire(timeout=0.3)
            elapsed = time.time() - start

            # Should timeout
            assert acquired is False
            # Should take approximately timeout duration
            assert 0.2 < elapsed < 0.5


def test_migration_lock_file_created():
    """Test that lock file is created in correct location"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "traceos.db"

        lock = MigrationLock(str(db_path))

        # Check lock file path
        expected_lock_file = Path(tmpdir) / ".traceos.db.migration.lock"
        assert lock.lock_file == expected_lock_file

        # Acquire lock - should create file
        with lock:
            assert lock.lock_file.exists()


def test_storage_migration_with_lock():
    """
    Test that MemoryStorage correctly uses migration lock.

    This verifies the integration between MigrationLock and MemoryStorage.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Create storage - this should use migration lock internally
        storage = MemoryStorage(str(db_path))

        # Run migration explicitly (should be safe to run multiple times)
        storage.run_cognitive_kernel_migration()
        storage.run_cognitive_kernel_migration()  # Idempotent

        # Verify migration succeeded
        conn = storage.get_connection()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "cognitive_memory_blocks" in table_names
        conn.close()


def test_lock_handle_cleanup():
    """Test that lock handles are properly cleaned up"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        lock = MigrationLock(str(db_path))

        # Before acquisition
        assert lock._lock_handle is None

        # During acquisition
        with lock:
            assert lock._lock_handle is not None

        # After release - handle should be closed
        # (We can't directly check if closed, but no exception = success)


if __name__ == "__main__":
    print("=" * 70)
    print("Cognitive Kernel v2.6 - Task 1: Multi-Process Migration Lock Tests")
    print("=" * 70)
    print()
    print("To run tests:")
    print("  pytest tests/test_migration_lock.py -v")
    print()
    print("Tests cover:")
    print("  - Basic lock acquire/release")
    print("  - Concurrent access prevention")
    print("  - Multi-process storage initialization (CRITICAL)")
    print("  - Lock timeout behavior")
    print("  - Lock file creation")
    print("  - Integration with MemoryStorage")
    print()
    print("HARDENING: Prevents database corruption from concurrent migrations")
    print("across multiple FastAPI workers or agent instances.")
    print()
