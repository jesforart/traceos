"""
Compression engine for MemAgent.

Handles compression of trace events into compact memory summaries.
"""

from .engine import CompressionEngine
from .trace_client import TraceClient

__all__ = ['CompressionEngine', 'TraceClient']
