#!/usr/bin/env python3
"""
Trace HTTP Wrapper - Entry point

Starts FastAPI server on port 8787 to expose Trace MCP via REST API.
"""

import uvicorn
import sys
import logging

logger = logging.getLogger(__name__)


def main():
    """Start the Trace HTTP Wrapper server."""
    logger.info("Starting Trace HTTP Wrapper on port 8787...")

    try:
        uvicorn.run(
            "trace_wrapper.server:app",
            host="0.0.0.0",
            port=8787,
            log_level="info",
            reload=False  # Set to True for development
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down Trace HTTP Wrapper...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
