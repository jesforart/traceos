"""
TraceOS Application Lifespan Manager - Iron Monolith + v2.6 Hardening

Handles startup initialization and shutdown cleanup for the unified runtime.

IRON MONOLITH:
- SQLite WAL mode initialization
- ProcessPool creation for AI inference
- Single unified application

V2.6 HARDENING:
- Multi-process migration locking (portalocker)
- Automatic vector checksums
- Explicit Parquet writer cleanup
- Global storage singleton

Critical for:
- Database migration verification with interprocess locks
- Non-blocking AI inference via ProcessPool
- Proper resource cleanup on shutdown
"""

from __future__ import annotations
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor
from typing import AsyncGenerator
import sqlite3
import logging
from pathlib import Path

from fastapi import FastAPI
from traceos.globals import TraceOSGlobals

logger = logging.getLogger("traceos.lifespan")


def _initialize_database(db_path: str = "data/tracememory.db") -> sqlite3.Connection:
    """
    Initialize SQLite connection with performance optimizations.

    IRON MONOLITH: WAL Mode Benefits
    - Concurrent reads during writes
    - Better crash recovery
    - Improved write performance

    V2.6 HARDENING: Uses existing MemoryStorage initialization

    Args:
        db_path: Path to SQLite database file

    Returns:
        Configured SQLite connection
    """
    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)

    # Performance PRAGMAs - ORDER MATTERS (from Iron Monolith spec)
    conn.execute("PRAGMA journal_mode=WAL;")        # Write-Ahead Logging
    conn.execute("PRAGMA synchronous=NORMAL;")      # Balance safety/speed
    conn.execute("PRAGMA busy_timeout=5000;")       # 5s wait before SQLITE_BUSY
    conn.execute("PRAGMA cache_size=-64000;")       # 64MB cache
    conn.execute("PRAGMA temp_store=MEMORY;")       # Temp tables in RAM
    conn.execute("PRAGMA mmap_size=268435456;")     # 256MB memory-mapped I/O

    # Enable foreign keys for data integrity
    conn.execute("PRAGMA foreign_keys=ON;")

    # Row factory for dict-like access
    conn.row_factory = sqlite3.Row

    logger.info(f"Database initialized: {db_path} (WAL mode enabled)")
    return conn


def _initialize_ai_pool(max_workers: int = 1) -> ProcessPoolExecutor:
    """
    Create ProcessPoolExecutor for AI inference.

    IRON MONOLITH: Why ProcessPool instead of ThreadPool
    - Python GIL blocks threads during CPU-intensive operations
    - sentence-transformers encode() is CPU-bound
    - ProcessPool runs in separate process, bypassing GIL
    - Keeps FastAPI event loop responsive during inference

    Args:
        max_workers: Number of worker processes (1 is usually sufficient)

    Returns:
        Configured ProcessPoolExecutor
    """
    pool = ProcessPoolExecutor(max_workers=max_workers)
    logger.info(f"AI Process Pool initialized: {max_workers} worker(s)")
    return pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager - Iron Monolith + v2.6 Hardening.

    Startup:
    1. Initialize SQLite with WAL mode
    2. Create MemoryStorage with v2.6 migration locks
    3. Initialize TelemetryStore (v2.6 Parquet writer)
    4. Create DualDNAEngine
    5. Initialize GeminiCritic
    6. Create AI ProcessPool for non-blocking inference

    Shutdown:
    1. Shutdown ProcessPool gracefully
    2. Close all Parquet writers (v2.6 Task 3)
    3. Close database connection
    """
    logger.info("=" * 70)
    logger.info("TraceOS Iron Monolith + v2.6 Hardening Starting...")
    logger.info("=" * 70)

    # === STARTUP ===
    try:
        # 1. Initialize database with WAL mode (Iron Monolith)
        logger.info("📊 Initializing database with WAL mode...")
        TraceOSGlobals.db_connection = _initialize_database()

        # 2. Initialize MemoryStorage (v2.6 hardening with migration locks)
        logger.info("🔧 Initializing MemoryStorage with v2.6 hardening...")
        from tracememory.storage.memory_storage import MemoryStorage
        TraceOSGlobals.memory_storage = MemoryStorage()

        # Run Cognitive Kernel migration with interprocess lock (v2.6 Task 1)
        TraceOSGlobals.memory_storage.run_cognitive_kernel_migration()

        # 3. Initialize TelemetryStore (v2.6 Task 3 - Parquet lifecycle)
        logger.info("🗂️  Initializing TelemetryStore...")
        from tracememory.storage.telemetry_store import TelemetryStore
        TraceOSGlobals.telemetry_store = TelemetryStore(base_path="data/telemetry")

        # 4. Initialize DualDNAEngine
        logger.info("🧬 Initializing DualDNAEngine...")
        from tracememory.dual_dna.engine import DualDNAEngine
        TraceOSGlobals.dual_dna_engine = DualDNAEngine(
            memory_storage=TraceOSGlobals.memory_storage,
            telemetry_store=TraceOSGlobals.telemetry_store
        )

        # 5. Initialize GeminiCritic (v2.6 Task 2 - mock mode fallback)
        logger.info("🎨 Initializing GeminiCritic...")
        from tracememory.critic.gemini_critic import GeminiCritic
        try:
            TraceOSGlobals.critic = GeminiCritic(mock_mode=False)
            logger.info("   ✓ Gemini API mode enabled")
        except ValueError as e:
            logger.warning(f"   ⚠️  Gemini API key not found: {e}")
            logger.warning(f"   ⚠️  Falling back to MOCK MODE")
            TraceOSGlobals.critic = GeminiCritic(mock_mode=True)

        # 6. Initialize AI ProcessPool (Iron Monolith - non-blocking inference)
        logger.info("⚡ Initializing AI Process Pool...")
        TraceOSGlobals.ai_process_pool = _initialize_ai_pool(max_workers=1)

        # Mark as ready
        TraceOSGlobals.is_initialized = True
        logger.info("=" * 70)
        logger.info("✓ TraceOS Iron Monolith ready on port 8000")
        logger.info("✓ v2.6 Hardening features active:")
        logger.info("  - Multi-process migration locking")
        logger.info("  - Automatic vector checksums")
        logger.info("  - Explicit Parquet lifecycle")
        logger.info("  - Global storage singleton")
        logger.info("  - Non-blocking AI inference (ProcessPool)")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield  # Application runs here

    # === SHUTDOWN ===
    logger.info("=" * 70)
    logger.info("TraceOS shutting down...")
    logger.info("=" * 70)

    # V2.6 Task 3: Close all Parquet writers explicitly
    if TraceOSGlobals.telemetry_store:
        logger.info("🗂️  Closing Parquet writers...")
        TraceOSGlobals.telemetry_store.close_all_sessions()

    # Iron Monolith: Shutdown AI ProcessPool
    if TraceOSGlobals.ai_process_pool:
        logger.info("⚡ Shutting down AI Process Pool...")
        TraceOSGlobals.ai_process_pool.shutdown(wait=True)
        logger.info("   ✓ AI Process Pool shutdown complete")

    # Close database connection
    if TraceOSGlobals.db_connection:
        logger.info("📊 Closing database connection...")
        TraceOSGlobals.db_connection.close()
        logger.info("   ✓ Database connection closed")

    TraceOSGlobals.is_initialized = False
    logger.info("=" * 70)
    logger.info("✓ TraceOS shutdown complete")
    logger.info("=" * 70)
