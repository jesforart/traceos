"""
Configuration settings for MemAgent service
"""

from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Service
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_VERSION: str = "v1"
    
    # Trace Integration
    TRACE_URL: str = "http://localhost:8787"
    TRACE_TIMEOUT: int = 30
    
    # Storage
    STORAGE_PATH: Path = Path.home() / ".memagent"
    MAX_MEMORY_BLOCK_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Compression
    USE_HF_MODEL: bool = True
    HF_MODEL_PATH: str = "driaforall/mem-agent"
    FALLBACK_TO_CLAUDE: bool = True
    ANTHROPIC_API_KEY: str = ""
    
    MAX_EVENTS_PER_COMPRESSION: int = 500
    TARGET_SUMMARY_TOKENS: int = 512
    COMPRESSION_CACHE_TTL: int = 3600  # 1 hour
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False  # MVP: disabled
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Modifiers
    MODIFIER_VALUE_MIN: float = 0.0
    MODIFIER_VALUE_MAX: float = 1.0
    
    class Config:
        env_file = ".env"

settings = Settings()
