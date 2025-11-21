"""
FastAPI server for Trace HTTP Wrapper.

Exposes Trace MCP server via REST API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from trace_wrapper.mcp_client import MCPClient
from trace_wrapper.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global MCP client instance
mcp_client: MCPClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown.

    Starts Trace MCP server on startup and stops it on shutdown.
    """
    global mcp_client

    # Startup
    logger.info("Starting Trace HTTP Wrapper...")
    try:
        mcp_client = MCPClient()
        await mcp_client.start()
        logger.info("Trace MCP client started successfully")
    except Exception as e:
        logger.error(f"Failed to start Trace MCP client: {e}")
        # Don't fail startup - allow wrapper to run in degraded mode
        mcp_client = None

    yield

    # Shutdown
    logger.info("Shutting down Trace HTTP Wrapper...")
    if mcp_client:
        try:
            await mcp_client.stop()
            logger.info("Trace MCP client stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Trace MCP client: {e}")


# Create FastAPI application
app = FastAPI(
    title="Trace HTTP Wrapper",
    description="REST API wrapper for Trace MCP server",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        Service information
    """
    return {
        "service": "trace-http-wrapper",
        "version": "1.0.0",
        "description": "REST API wrapper for Trace MCP server",
        "endpoints": {
            "health": "/v1/health",
            "sessions": "/v1/sessions",
            "events": "/v1/sessions/{session_id}/events",
            "provenance": "/v1/sessions/{session_id}/provenance"
        },
        "docs": "/docs"
    }
