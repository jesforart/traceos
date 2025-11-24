"""
Agent Orchestrator - Main entry point.

Starts FastAPI server with Agent Orchestrator.
"""

import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orchestrator.core import Orchestrator
from orchestrator.routes import router, set_orchestrator
from orchestrator.agents import ExampleAgent
from orchestrator.dependencies import initialize_storage, shutdown_storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown.

    HARDENING v2.6 - Task 2: Global storage initialization

    Startup:
    - Initialize global storage (MemoryStorage, TelemetryStore, DualDNAEngine, Critic)
    - Initialize orchestrator
    - Register example agents

    Shutdown:
    - Close all Parquet writers (Task 3)
    - Close database connections
    - Clean up resources
    """
    logger.info("Starting Agent Orchestrator...")

    # HARDENING v2.6 - Task 2: Initialize global storage ONCE on startup
    initialize_storage(
        db_path="data/tracememory.db",
        telemetry_path="data/telemetry",
        critic_mock_mode=False  # Set to True to avoid Gemini API calls
    )

    # Initialize orchestrator
    orchestrator = Orchestrator(
        memagent_url="http://localhost:8000",
        trace_url="http://localhost:8787"
    )

    # Set orchestrator for routes
    set_orchestrator(orchestrator)

    # Register example agent
    example_agent = ExampleAgent()
    orchestrator.register_agent(example_agent)

    logger.info("Agent Orchestrator started successfully")
    logger.info(f"Registered agents: {[a.agent_id for a in orchestrator.list_agents()]}")

    # Check integrations
    integration_health = await orchestrator.integrations.check_integrations()
    logger.info(f"Integration health: {integration_health}")

    yield

    # Shutdown
    logger.info("Shutting down Agent Orchestrator...")

    # HARDENING v2.6 - Task 2 & 3: Explicit cleanup of global storage
    shutdown_storage()


# Create FastAPI app
app = FastAPI(
    title="Agent Orchestrator",
    description="Multi-agent coordination for TraceOS",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/v1")


def main():
    """Run the server."""
    logger.info("=" * 60)
    logger.info("Agent Orchestrator")
    logger.info("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8888,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()
