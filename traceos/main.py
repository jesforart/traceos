"""
TraceOS Iron Monolith – Unified Entry Point

This is THE entry point for TraceOS v2.1 Iron Monolith + v2.6 Hardening.
All previous separate services (TraceMemory, Orchestrator) are now routers.

ARCHITECTURE:
- Single FastAPI application on port 8000
- TraceMemory routes: /v1/memory/*
- Orchestrator routes: /v1/orchestrate/*
- Critic routes: /v1/critic/*
- Symbiotic routes: /v1/symbiotic/*

V2.6 HARDENING:
- Multi-process safe migrations
- Global storage singleton
- Automatic vector checksums
- Explicit Parquet lifecycle

IRON MONOLITH:
- ProcessPool for non-blocking AI
- SQLite WAL mode
- Real sentence-transformers embeddings

Run with:
    uvicorn traceos.main:app --host 0.0.0.0 --port 8000

Or with auto-reload for development:
    uvicorn traceos.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from traceos.lifespan import lifespan

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout
)
logger = logging.getLogger("traceos")

# === CREATE UNIFIED APPLICATION ===
app = FastAPI(
    title="TraceOS Core",
    description="Iron Monolith + v2.6 Hardening – Unified Creative Intelligence Runtime",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# === CORS MIDDLEWARE ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MOUNT ROUTERS ===
# These imports must happen after app creation to avoid circular imports

# TraceMemory routes (was port 8000) - mounted under /v1
logger.info("📦 Mounting TraceMemory routes...")
try:
    from tracememory.api.routes import router as memory_router
    app.include_router(
        memory_router,
        prefix="/v1",  # Existing routes stay at /v1/...
        tags=["Memory"]
    )
    logger.info("   ✓ Core memory routes mounted")
except Exception as e:
    logger.error(f"   ❌ Failed to mount memory routes: {e}")

# SVG routes
try:
    from tracememory.api.svg_routes import router as svg_router
    app.include_router(
        svg_router,
        prefix="/v1",
        tags=["SVG"]
    )
    logger.info("   ✓ SVG routes mounted")
except Exception as e:
    logger.error(f"   ❌ Failed to mount SVG routes: {e}")

# Drawing routes
try:
    from tracememory.api.drawing_routes import router as drawing_router
    app.include_router(
        drawing_router,
        prefix="/v1",
        tags=["Drawing"]
    )
    logger.info("   ✓ Drawing routes mounted")
except Exception as e:
    logger.error(f"   ❌ Failed to mount drawing routes: {e}")

# Semantic routes
try:
    from tracememory.api.semantic_routes import router as semantic_router
    app.include_router(
        semantic_router,
        prefix="/v1",
        tags=["Semantic"]
    )
    logger.info("   ✓ Semantic routes mounted")
except Exception as e:
    logger.error(f"   ❌ Failed to mount semantic routes: {e}")

# Calibration routes
try:
    from tracememory.api.calibration_routes import router as calibration_router
    app.include_router(
        calibration_router,
        prefix="/v1",
        tags=["Calibration"]
    )
    logger.info("   ✓ Calibration routes mounted")
except Exception as e:
    logger.error(f"   ❌ Failed to mount calibration routes: {e}")

# Replay routes
try:
    from tracememory.replay.routes import router as replay_router
    app.include_router(
        replay_router,
        prefix="/v1",
        tags=["Replay"]
    )
    logger.info("   ✓ Replay routes mounted")
except Exception as e:
    logger.error(f"   ❌ Failed to mount replay routes: {e}")

# Critic routes (v2.6 Gemini Critic)
try:
    from tracememory.api.critic_routes import router as critic_router
    app.include_router(
        critic_router,
        tags=["Critic"]
    )
    logger.info("   ✓ Critic routes mounted")
except Exception as e:
    logger.error(f"   ❌ Failed to mount critic routes: {e}")

# Gut valuation routes (v3.0 intent_gut_taste_001)
try:
    from tracememory.api.critic_routes import gut_router
    app.include_router(
        gut_router,
        tags=["Gut"]
    )
    logger.info("   ✓ Gut valuation routes mounted (WebSocket + REST)")
except Exception as e:
    logger.error(f"   ❌ Failed to mount gut routes: {e}")

# Orchestrator routes (was port 8888) - mounted under /v1/orchestrate
logger.info("🎭 Mounting Orchestrator routes...")
try:
    from orchestrator.routes import router as orchestrator_router
    app.include_router(
        orchestrator_router,
        prefix="/v1/orchestrate",
        tags=["Orchestration"]
    )
    logger.info("   ✓ Orchestrator routes mounted")
except Exception as e:
    logger.error(f"   ❌ Failed to mount orchestrator routes: {e}")

# TraceOS Protocol routes (Intent → Derive → Evaluate → Codify)
logger.info("🔧 Mounting Protocol routes...")
try:
    from traceos.protocol.routes import router as protocol_router
    app.include_router(
        protocol_router,
        prefix="/v1/trace",
        tags=["Protocol"]
    )
    logger.info("   ✓ Protocol routes mounted (/v1/trace/*)")
except Exception as e:
    logger.error(f"   ❌ Failed to mount protocol routes: {e}")


# === HEALTH CHECK ENDPOINTS ===
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint – confirms TraceOS is running."""
    return {
        "service": "TraceOS Core",
        "version": "2.1.0",
        "codename": "Iron Monolith + v2.6 Hardening",
        "status": "operational",
        "architecture": "unified_monolith",
        "features": [
            "multi_process_safe_migrations",
            "automatic_vector_checksums",
            "explicit_parquet_lifecycle",
            "global_storage_singleton",
            "non_blocking_ai_inference"
        ]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    IRON MONOLITH: Must respond in <10ms even during heavy AI inference.
    This validates ProcessPool is working (not blocking main thread).

    V2.6 HARDENING: Includes storage initialization status.
    """
    from traceos.globals import TraceOSGlobals

    return {
        "status": "healthy",
        "initialized": TraceOSGlobals.is_initialized,
        "database": "connected" if TraceOSGlobals.db_connection else "disconnected",
        "memory_storage": "ready" if TraceOSGlobals.memory_storage else "not_initialized",
        "telemetry_store": "ready" if TraceOSGlobals.telemetry_store else "not_initialized",
        "dual_dna_engine": "ready" if TraceOSGlobals.dual_dna_engine else "not_initialized",
        "critic": "ready" if TraceOSGlobals.critic else "not_initialized",
        "ai_pool": "ready" if TraceOSGlobals.ai_process_pool else "not_initialized"
    }


@app.get("/v1/status", tags=["Health"])
async def detailed_status():
    """Detailed system status including database stats and v2.6 features."""
    from traceos.globals import TraceOSGlobals

    stats = {}

    # Database statistics
    if TraceOSGlobals.db_connection:
        try:
            # Check Cognitive Kernel tables (v2.6)
            cursor = TraceOSGlobals.db_connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'cognitive_%'"
            )
            cognitive_tables = [row[0] for row in cursor.fetchall()]

            # Get schema version
            cursor = TraceOSGlobals.db_connection.execute(
                "SELECT version, description FROM schema_versions ORDER BY version DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                stats["schema_version"] = row["version"]
                stats["schema_description"] = row["description"]

            stats["cognitive_kernel_tables"] = cognitive_tables

        except Exception as e:
            stats["error"] = str(e)

    # Telemetry statistics (v2.6 Task 3)
    if TraceOSGlobals.telemetry_store:
        try:
            open_sessions = TraceOSGlobals.telemetry_store.get_open_sessions()
            stats["open_parquet_sessions"] = len(open_sessions)
            stats["open_session_ids"] = open_sessions
        except Exception as e:
            stats["telemetry_error"] = str(e)

    # Critic status (v2.6)
    if TraceOSGlobals.critic:
        stats["critic_mock_mode"] = TraceOSGlobals.critic.mock_mode

    return {
        "service": "TraceOS Core",
        "version": "2.1.0",
        "architecture": "Iron Monolith + v2.6 Hardening",
        "stats": stats,
        "hardening_features": {
            "task_1_migration_locking": "active",
            "task_2_global_storage": "active",
            "task_3_parquet_lifecycle": "active",
            "task_4_vector_checksums": "active",
            "task_5_enhanced_errors": "active",
            "iron_monolith_ai_pool": "active"
        }
    }


# === DEVELOPMENT ENTRY POINT ===
if __name__ == "__main__":
    import uvicorn
    logger.info("=" * 70)
    logger.info("Starting TraceOS Core in development mode")
    logger.info("Iron Monolith + v2.6 Hardening")
    logger.info("=" * 70)
    uvicorn.run(
        "traceos.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
