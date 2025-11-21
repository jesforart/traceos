"""
MemAgent FastAPI Application

Main entry point for the MemAgent service.
Provides REST API for memory management, session tracking,
and design variation control.
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from api.routes import router
from api.svg_routes import router as svg_router
from api.drawing_routes import router as drawing_router
from api.semantic_routes import router as semantic_router
from api.calibration_routes import router as calibration_router
from replay.routes import router as replay_router
from api.errors import MemAgentException, ErrorResponse
from config import settings

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

def setup_logging():
    """
    Configure logging for the application.

    Logs to stdout with structured format:
    [timestamp] [level] [module] message
    """
    log_format = (
        "[%(asctime)s] [%(levelname)8s] [%(name)s] %(message)s"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )

    # Set library log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # Set MemAgent components to DEBUG for development
    logging.getLogger("memagent").setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured")


# ============================================================
# APPLICATION LIFECYCLE
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Startup:
    - Configure logging
    - Initialize storage
    - Log startup info

    Shutdown:
    - Clean up resources
    - Log shutdown
    """
    # Startup
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("MemAgent Service Starting")
    logger.info("=" * 60)
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Storage Path: {settings.STORAGE_PATH}")
    logger.info(f"HF Model: {settings.HF_MODEL_PATH if settings.USE_HF_MODEL else 'Disabled'}")
    logger.info(f"Trace URL: {settings.TRACE_URL}")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("MemAgent Service Shutting Down")


# ============================================================
# APPLICATION SETUP
# ============================================================

app = FastAPI(
    title="MemAgent API",
    description=(
        "Memory management service for Symbiotic Design Engineering. "
        "Provides compressed session memory, asset tracking, and provenance."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================
# MIDDLEWARE
# ============================================================

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # Self
        "http://localhost:8787",  # Trace MCP
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests.

    Logs:
    - Method and path
    - Client IP
    - Response status
    - Duration
    """
    logger = logging.getLogger("memagent.main")
    start_time = datetime.utcnow()

    # Log request
    logger.info(
        f"{request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    # Process request
    response = await call_next(request)

    # Log response
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed with {response.status_code} "
        f"in {duration_ms:.2f}ms"
    )

    return response


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(MemAgentException)
async def memagent_exception_handler(request: Request, exc: MemAgentException):
    """
    Handle MemAgent-specific exceptions globally.

    Returns structured error response.
    """
    logger = logging.getLogger(__name__)
    logger.warning(
        f"MemAgent exception: {exc.error_code} - {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code,
            message=exc.detail,
            detail=exc.detail_msg,
            hint=exc.hint,
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.

    Logs full traceback and returns generic error.
    """
    logger = logging.getLogger(__name__)
    logger.error(
        f"Unexpected error in {request.method} {request.url.path}: {exc}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================
# ROUTES
# ============================================================

# Include API routers
app.include_router(router)
app.include_router(svg_router)
app.include_router(drawing_router)
app.include_router(semantic_router)
app.include_router(calibration_router)
app.include_router(replay_router)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with service info.
    """
    return {
        "service": "MemAgent",
        "version": "1.0.0",
        "api_version": settings.API_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/v1/health"
    }


# ============================================================
# DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
