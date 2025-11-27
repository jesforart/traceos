"""
Dependency Injection for TraceOS Cognitive Kernel v2.6

HARDENING v2.6 - Task 2: Global Storage Instance with Dependency Injection

Problem: Every FastAPI route call was creating new MemoryStorage instance,
running migrations, PRAGMAs, and locking setup repeatedly.

Solution: Single global instance initialized on startup, injected via
FastAPI dependencies.
"""

import sys
import logging
from typing import Optional
from pathlib import Path

# Add tracememory to path for imports
tracememory_path = Path(__file__).parent.parent.parent / "tracememory"
if str(tracememory_path) not in sys.path:
    sys.path.insert(0, str(tracememory_path))

from tracememory.storage.memory_storage import MemoryStorage
from tracememory.storage.telemetry_store import TelemetryStore
from tracememory.dual_dna.engine import DualDNAEngine
from tracememory.critic.gemini_critic import GeminiCritic

logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL INSTANCES (initialized on startup)
# ============================================================================

_storage: Optional[MemoryStorage] = None
_telemetry: Optional[TelemetryStore] = None
_dual_dna_engine: Optional[DualDNAEngine] = None
_critic: Optional[GeminiCritic] = None


def initialize_storage(
    db_path: str = "data/tracememory.db",
    telemetry_path: str = "data/telemetry",
    critic_mock_mode: bool = False
):
    """
    Initialize global storage instances.

    Called once during application startup via lifespan hook.

    HARDENING v2.6 - Task 2: Single global instance prevents:
    - Repeated migration runs
    - Multiple database connections
    - Lock contention
    - Resource waste

    Args:
        db_path: Path to SQLite database
        telemetry_path: Path to Parquet telemetry storage
        critic_mock_mode: If True, use mock critic (no API calls)
    """
    global _storage, _telemetry, _dual_dna_engine, _critic

    logger.info("🔧 Initializing global storage instances...")
    logger.info(f"   Database: {db_path}")
    logger.info(f"   Telemetry: {telemetry_path}")

    # Initialize MemoryStorage (runs migration once with interprocess lock)
    _storage = MemoryStorage(db_path)
    _storage.run_cognitive_kernel_migration()

    # Initialize TelemetryStore
    _telemetry = TelemetryStore(telemetry_path)

    # Initialize DualDNAEngine
    _dual_dna_engine = DualDNAEngine(_storage, _telemetry)

    # Initialize GeminiCritic
    try:
        _critic = GeminiCritic(mock_mode=critic_mock_mode)
        logger.info(f"   Critic: {'MOCK MODE' if critic_mock_mode else 'Gemini API'}")
    except ValueError as e:
        logger.warning(f"   Critic initialization warning: {e}")
        logger.warning(f"   Falling back to MOCK MODE")
        _critic = GeminiCritic(mock_mode=True)

    logger.info("✓ Global storage initialized successfully")


def get_storage() -> MemoryStorage:
    """
    Dependency: Get global storage instance.

    Usage in FastAPI routes:
        @router.get("/")
        async def my_route(storage: MemoryStorage = Depends(get_storage)):
            # Use storage...

    Returns:
        Global MemoryStorage instance

    Raises:
        RuntimeError: If storage not initialized (call initialize_storage() first)
    """
    if _storage is None:
        raise RuntimeError(
            "Storage not initialized. Call initialize_storage() during startup."
        )
    return _storage


def get_telemetry() -> TelemetryStore:
    """
    Dependency: Get global telemetry store.

    Returns:
        Global TelemetryStore instance

    Raises:
        RuntimeError: If telemetry not initialized
    """
    if _telemetry is None:
        raise RuntimeError(
            "Telemetry not initialized. Call initialize_storage() during startup."
        )
    return _telemetry


def get_dual_dna_engine() -> DualDNAEngine:
    """
    Dependency: Get global Dual DNA engine.

    Returns:
        Global DualDNAEngine instance

    Raises:
        RuntimeError: If engine not initialized
    """
    if _dual_dna_engine is None:
        raise RuntimeError(
            "DualDNAEngine not initialized. Call initialize_storage() during startup."
        )
    return _dual_dna_engine


def get_critic() -> GeminiCritic:
    """
    Dependency: Get global Gemini critic.

    Returns:
        Global GeminiCritic instance

    Raises:
        RuntimeError: If critic not initialized
    """
    if _critic is None:
        raise RuntimeError(
            "GeminiCritic not initialized. Call initialize_storage() during startup."
        )
    return _critic


def shutdown_storage():
    """
    Cleanup global storage instances.

    Called during application shutdown via lifespan hook.

    HARDENING v2.6 - Task 2 & 3: Explicit cleanup:
    - Closes all open Parquet writers
    - Closes database connection
    - Releases resources
    """
    global _storage, _telemetry, _dual_dna_engine, _critic

    logger.info("🔧 Shutting down storage...")

    # Task 3: Close all Parquet writers explicitly
    if _telemetry:
        _telemetry.close_all_sessions()

    # Close database connection
    if _storage:
        try:
            _storage._conn.close()
            logger.info(f"   ✓ Database connection closed")
        except Exception as e:
            logger.warning(f"   ⚠️ Error closing database: {e}")

    # Clear global references
    _storage = None
    _telemetry = None
    _dual_dna_engine = None
    _critic = None

    logger.info("✓ Storage shutdown complete")


def get_storage_stats() -> dict:
    """
    Get statistics about global storage instances.

    Useful for health checks and monitoring.

    Returns:
        Dict with storage statistics
    """
    return {
        "storage_initialized": _storage is not None,
        "telemetry_initialized": _telemetry is not None,
        "dual_dna_initialized": _dual_dna_engine is not None,
        "critic_initialized": _critic is not None,
        "critic_mock_mode": _critic.mock_mode if _critic else None,
        "open_parquet_sessions": len(_telemetry.get_open_sessions()) if _telemetry else 0
    }
