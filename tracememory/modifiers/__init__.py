"""
Modifier Engine - SVG transformation system for MemAgent.

Provides 12 modifiers for SVG manipulation:
- stroke_weight, fill_opacity, hue_shift
- scale, rotate, brightness, saturation, contrast
- blur, x_offset, y_offset, skew
"""

from modifiers.base import BaseModifier, ModifierRegistry
from modifiers.engine import ModifierEngine

__all__ = [
    "BaseModifier",
    "ModifierRegistry",
    "ModifierEngine",
]
