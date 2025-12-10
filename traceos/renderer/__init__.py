"""
TraceOS Renderer Module

Backend rasterization of stroke plans into RGBA images.

NOT a realtime UI renderer. This is used for:
- Internal imagination snapshots
- Provenance artifacts
- Future computer-vision analysis by Eyes

@provenance traceos_renderer_v1
@organ visual
"""

from .layers import Layer
from .canvas import Canvas

__all__ = [
    "Layer",
    "Canvas"
]
