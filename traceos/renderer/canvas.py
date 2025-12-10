"""
Canvas - Backend Rasterizer

This acts as the 'Imagination' of TraceOS - rendering stroke plans into
pixels for internal review by the Eyes organ and for provenance snapshots.

This is NOT the real-time iPad/Wacom renderer. It is a backend renderer
for:
- visual tests
- offline analysis
- future computer-vision pipelines

@provenance traceos_renderer_v1
@organ visual
"""

import logging
from typing import List
from math import pow

from PIL import Image, ImageDraw

from .layers import Layer
from traceos.hands.schemas import StrokePlan

logger = logging.getLogger(__name__)


class Canvas:
    """
    Backend rasterization surface.

    Can maintain multiple transparent layers and composite them into a
    final RGBA image.
    """

    def __init__(self, width: int = 1024, height: int = 1024, bg_color="white"):
        self.width = width
        self.height = height
        # Base canvas; we keep alpha so compositing is predictable
        self.base = Image.new("RGBA", (width, height), bg_color)
        self.layers: List[Layer] = []
        logger.info(f"Canvas initialized: {width}x{height}")

    def add_layer(self, name: str) -> Layer:
        """Add a new transparent layer to the canvas."""
        layer = Layer(name, self.width, self.height)
        self.layers.append(layer)
        logger.debug(f"Added layer '{name}'")
        return layer

    def render_stroke(self, layer: Layer, plan: StrokePlan) -> None:
        """
        Render a biological stroke plan into pixels.

        Uses a non-linear pressure mapping (roughly sigmoid-like) to
        simulate real nib spreading, with opacity also linked to pressure.
        """
        draw = ImageDraw.Draw(layer.image)
        points = plan.points

        if len(points) < 2:
            logger.warning(f"Stroke {plan.stroke_id} has fewer than 2 points; skipping render")
            return

        # Base brush size; pressure will modulate this
        base_width = 5.0

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            # Non-linear pressure curve:
            # Emphasize differences at the high end (ink "blooms" when pressing hard)
            pressure = max(0.0, min(1.0, p1.pressure))
            pressure_mod = pow(pressure, 1.5) * 2.0  # super-linear scaling

            width = max(1.0, base_width * pressure_mod)

            # Opacity also depends on pressure
            alpha = int(255 * pressure)

            draw.line(
                [(p1.x, p1.y), (p2.x, p2.y)],
                fill=(0, 0, 0, alpha),  # Black ink, pressure-driven opacity
                width=int(width)
            )

        logger.debug(f"Rendered stroke {plan.stroke_id} to layer '{layer.name}'")

    def composite(self) -> Image.Image:
        """
        Flatten all visible layers onto the base canvas.
        """
        final = self.base.copy()

        for layer in self.layers:
            if not layer.is_visible:
                continue
            # For now we don't re-scale alpha per layer.opacity; can be added later
            final.alpha_composite(layer.image)

        return final
