"""
Error handling for MemAgent service
"""

from fastapi import HTTPException, status
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ErrorCode(str, Enum):
    # Session errors
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_ALREADY_EXISTS = "SESSION_ALREADY_EXISTS"
    
    # Asset errors
    ASSET_NOT_FOUND = "ASSET_NOT_FOUND"
    ASSET_INVALID = "ASSET_INVALID"
    ASSET_TOO_LARGE = "ASSET_TOO_LARGE"
    
    # Modifier errors
    MODIFIER_UNKNOWN = "MODIFIER_UNKNOWN"
    MODIFIER_VALUE_INVALID = "MODIFIER_VALUE_INVALID"
    MODIFIER_FAILED = "MODIFIER_FAILED"
    
    # Compression errors
    COMPRESSION_FAILED = "COMPRESSION_FAILED"
    COMPRESSION_TIMEOUT = "COMPRESSION_TIMEOUT"
    
    # Storage errors
    STORAGE_ERROR = "STORAGE_ERROR"
    STORAGE_FULL = "STORAGE_FULL"
    
    # Trace errors
    TRACE_UNAVAILABLE = "TRACE_UNAVAILABLE"
    TRACE_ERROR = "TRACE_ERROR"
    
    # General
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"

class ErrorResponse(BaseModel):
    error: ErrorCode
    message: str
    detail: Optional[str] = None
    hint: Optional[str] = None
    timestamp: str

class MemAgentException(HTTPException):
    def __init__(
        self, 
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None,
        hint: Optional[str] = None
    ):
        self.error_code = error_code
        self.detail_msg = detail
        self.hint = hint
        super().__init__(status_code=status_code, detail=message)

# Exception handlers
class SessionNotFoundException(MemAgentException):
    def __init__(self, session_id: str):
        super().__init__(
            error_code=ErrorCode.SESSION_NOT_FOUND,
            message=f"Session not found: {session_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            hint="Create session first using POST /session/init"
        )

class ModifierNotFoundException(MemAgentException):
    def __init__(self, modifier: str):
        super().__init__(
            error_code=ErrorCode.MODIFIER_UNKNOWN,
            message=f"Unknown modifier: {modifier}",
            status_code=status.HTTP_400_BAD_REQUEST,
            hint="Available: stroke_weight, fill_opacity, hue_shift, scale"
        )

class CompressionFailedException(MemAgentException):
    def __init__(self, reason: str):
        super().__init__(
            error_code=ErrorCode.COMPRESSION_FAILED,
            message="Compression failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=reason,
            hint="Check logs for details, fallback to Claude API"
        )
