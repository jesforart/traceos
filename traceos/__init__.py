"""
TraceOS - Computational Psyche for Creative AI

Public Reference Implementation
Patent Pending: US Provisional 63/926,510

This package provides interface definitions and architecture specifications.
The core "Iron Monolith" inference engine is proprietary.
"""

__version__ = "0.9.0"
__author__ = "TraceOS LLC"
__license__ = "Proprietary"

from traceos.main import create_app

__all__ = ["create_app", "__version__"]
