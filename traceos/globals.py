"""
TraceOS Global Resource Container - Iron Monolith Architecture

This module provides shared state across the unified application,
eliminating the need for HTTP calls between Memory and Orchestrator.

Design Principle: Single-process shared state beats network serialization.

INTEGRATION: Works with v2.6 hardening (migration locks, checksums, lifecycle).
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from concurrent.futures import ProcessPoolExecutor
import sqlite3
import logging

if TYPE_CHECKING:
    from tracememory.storage.memory_storage import MemoryStorage
    from tracememory.storage.telemetry_store import TelemetryStore
    from tracememory.dual_dna.engine import DualDNAEngine
    from tracememory.critic.gemini_critic import GeminiCritic

logger = logging.getLogger("traceos.globals")


class TraceOSGlobals:
    """
    Centralized container for TraceOS runtime resources.

    Initialized during FastAPI lifespan startup.
    Accessed by any module that needs shared resources.

    IRON MONOLITH: Eliminates inter-service HTTP calls
    V2.6 HARDENING: Integrates with singleton pattern from orchestrator/dependencies.py

    Attributes:
        db_connection: Primary SQLite connection (WAL mode)
        memory_storage: MemoryStorage instance for direct access
        telemetry_store: TelemetryStore for Parquet operations
        dual_dna_engine: DualDNAEngine for vector computation
        critic: GeminiCritic for aesthetic evaluation
        ai_process_pool: ProcessPoolExecutor for non-blocking AI inference
        is_initialized: Flag indicating successful startup
    """

    # Database Layer
    db_connection: Optional[sqlite3.Connection] = None
    memory_storage: Optional["MemoryStorage"] = None
    telemetry_store: Optional["TelemetryStore"] = None

    # Intelligence Layer
    dual_dna_engine: Optional["DualDNAEngine"] = None
    critic: Optional["GeminiCritic"] = None

    # AI Inference Layer (ProcessPool to avoid GIL blocking)
    ai_process_pool: Optional[ProcessPoolExecutor] = None

    # Runtime State
    is_initialized: bool = False

    @classmethod
    def get_db(cls) -> sqlite3.Connection:
        """Get the shared database connection."""
        if cls.db_connection is None:
            raise RuntimeError("TraceOS not initialized. Call lifespan startup first.")
        return cls.db_connection

    @classmethod
    def get_memory_storage(cls) -> "MemoryStorage":
        """Get the shared MemoryStorage instance."""
        if cls.memory_storage is None:
            raise RuntimeError("TraceOS not initialized. Call lifespan startup first.")
        return cls.memory_storage

    @classmethod
    def get_telemetry_store(cls) -> "TelemetryStore":
        """Get the shared TelemetryStore instance."""
        if cls.telemetry_store is None:
            raise RuntimeError("TraceOS not initialized. Call lifespan startup first.")
        return cls.telemetry_store

    @classmethod
    def get_dual_dna_engine(cls) -> "DualDNAEngine":
        """Get the shared DualDNAEngine instance."""
        if cls.dual_dna_engine is None:
            raise RuntimeError("TraceOS not initialized. Call lifespan startup first.")
        return cls.dual_dna_engine

    @classmethod
    def get_critic(cls) -> "GeminiCritic":
        """Get the shared GeminiCritic instance."""
        if cls.critic is None:
            raise RuntimeError("TraceOS not initialized. Call lifespan startup first.")
        return cls.critic

    @classmethod
    def get_ai_pool(cls) -> ProcessPoolExecutor:
        """Get the AI inference process pool."""
        if cls.ai_process_pool is None:
            raise RuntimeError("TraceOS not initialized. Call lifespan startup first.")
        return cls.ai_process_pool


# Convenience alias
Globals = TraceOSGlobals
