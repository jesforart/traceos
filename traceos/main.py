"""
TraceOS Iron Monolith - Main Entry Point

This is the unified FastAPI application that runs all cognitive organs
in a single process for minimal latency.

Patent Pending: US Provisional 63/926,510
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from traceos.lifespan import lifespan


def create_app() -> FastAPI:
    """
    Create and configure the TraceOS FastAPI application.

    Returns:
        Configured FastAPI instance with all routes mounted.
    """
    app = FastAPI(
        title="TraceOS",
        description="Computational Psyche for Creative AI",
        version="0.9.0",
        lifespan=lifespan,
    )

    # CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "ok", "service": "TraceOS Iron Monolith"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    # Production routes (mounted in proprietary build):
    # - TraceMemory routes: /v1/memory/*
    # - Orchestrator routes: /v1/trace/*
    # - Critic routes: /v1/critic/*
    # - Renderer routes: /v1/render/*
    # - DNA routes: /v1/dna/*

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
