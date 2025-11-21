"""
Shared storage instances for drawing and semantic modules.

This module provides singleton instances of storage classes to ensure
all modules share the same data.
"""

from .stroke_storage import StrokeStorage
from .stroke_processor import StrokeProcessor
from .semantic_storage import SemanticStorage
from .auto_detector import AutoDetector

# Singleton instances
stroke_storage = StrokeStorage()
stroke_processor = StrokeProcessor()
semantic_storage = SemanticStorage()
auto_detector = AutoDetector()