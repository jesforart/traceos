"""
Renderer Layers

A single transparent layer in the creative stack.

@provenance traceos_renderer_v1
@organ visual
"""

from PIL import Image


class Layer:
    """A single transparency layer in the creative stack."""

    def __init__(self, name: str, width: int, height: int):
        self.name = name
        self.width = width
        self.height = height
        # RGBA for transparency support
        self.image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self.is_visible = True
        self.opacity = 1.0
