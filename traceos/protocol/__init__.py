"""
TraceOS Protocol Module

Implements the Intent → Derive → Test → Evaluate → Codify workflow.

Security Note: /v1/trace/* endpoints are for LOCAL DEVELOPMENT ONLY.
Do not expose these endpoints publicly without authentication.

@provenance traceos_protocol_v1
@organ kernel
"""

from .schemas import (
    Intent,
    DeriveOutput,
    TestOutput,
    EvaluateOutput,
    CodifyOutput,
    DegradedModeOutput
)
from .persistence import ProtocolStorage
from .intent import IntentHandler
from .derive import DeriveHandler
from .evaluate import EvaluateHandler
from .codify import CodifyHandler

__all__ = [
    "Intent",
    "DeriveOutput",
    "TestOutput",
    "EvaluateOutput",
    "CodifyOutput",
    "DegradedModeOutput",
    "ProtocolStorage",
    "IntentHandler",
    "DeriveHandler",
    "EvaluateHandler",
    "CodifyHandler",
]
