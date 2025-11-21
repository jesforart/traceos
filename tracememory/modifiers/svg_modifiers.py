"""
SVG Modifier Implementations.

12 modifiers for SVG transformation:
- stroke_weight, fill_opacity, hue_shift
- scale, rotate, brightness, saturation, contrast
- blur, x_offset, y_offset, skew
"""

import re
import colorsys
from typing import Tuple, Optional
from lxml import etree

from modifiers.base import BaseModifier, register_modifier


# =============================================================================
# Color Utilities
# =============================================================================

def parse_color(color_str: str) -> Optional[Tuple[int, int, int]]:
    """
    Parse CSS color string to RGB tuple.

    Supports:
    - Hex: #FF0000, #F00
    - RGB: rgb(255, 0, 0)
    - Named: red, blue, green, etc.

    Args:
        color_str: CSS color string

    Returns:
        (R, G, B) tuple (0-255) or None if unparseable
    """
    if not color_str:
        return None

    color_str = color_str.strip().lower()

    # Named colors (basic set)
    named_colors = {
        'red': (255, 0, 0), 'green': (0, 128, 0), 'blue': (0, 0, 255),
        'white': (255, 255, 255), 'black': (0, 0, 0), 'gray': (128, 128, 128),
        'yellow': (255, 255, 0), 'cyan': (0, 255, 255), 'magenta': (255, 0, 255),
        'orange': (255, 165, 0), 'purple': (128, 0, 128), 'brown': (165, 42, 42),
    }

    if color_str in named_colors:
        return named_colors[color_str]

    # Hex color: #RRGGBB or #RGB
    if color_str.startswith('#'):
        hex_str = color_str[1:]
        if len(hex_str) == 3:
            # #RGB -> #RRGGBB
            hex_str = ''.join([c*2 for c in hex_str])
        if len(hex_str) == 6:
            try:
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                return (r, g, b)
            except ValueError:
                return None

    # RGB color: rgb(r, g, b)
    rgb_match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return (r, g, b)

    return None


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB tuple to hex color string."""
    return f"#{r:02x}{g:02x}{b:02x}"


def adjust_hue(color_str: str, hue_shift: float) -> str:
    """
    Adjust hue of color by shift amount.

    Args:
        color_str: CSS color string
        hue_shift: Hue shift in range [-1.0, 1.0] (normalized)

    Returns:
        New color as hex string
    """
    rgb = parse_color(color_str)
    if not rgb:
        return color_str  # Return unchanged if unparseable

    # Convert to HSL
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # Shift hue (wrap around)
    h = (h + hue_shift) % 1.0

    # Convert back to RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    r, g, b = [int(x * 255) for x in (r, g, b)]

    return rgb_to_hex(r, g, b)


def adjust_brightness(color_str: str, brightness_delta: float) -> str:
    """
    Adjust brightness (lightness) of color.

    Args:
        color_str: CSS color string
        brightness_delta: Brightness adjustment [-1.0, 1.0]

    Returns:
        New color as hex string
    """
    rgb = parse_color(color_str)
    if not rgb:
        return color_str

    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # Adjust lightness
    l = max(0.0, min(1.0, l + brightness_delta))

    r, g, b = colorsys.hls_to_rgb(h, l, s)
    r, g, b = [int(x * 255) for x in (r, g, b)]

    return rgb_to_hex(r, g, b)


def adjust_saturation(color_str: str, saturation_mult: float) -> str:
    """
    Adjust saturation of color.

    Args:
        color_str: CSS color string
        saturation_mult: Saturation multiplier [0.0, 2.0]

    Returns:
        New color as hex string
    """
    rgb = parse_color(color_str)
    if not rgb:
        return color_str

    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # Adjust saturation
    s = max(0.0, min(1.0, s * saturation_mult))

    r, g, b = colorsys.hls_to_rgb(h, l, s)
    r, g, b = [int(x * 255) for x in (r, g, b)]

    return rgb_to_hex(r, g, b)


# =============================================================================
# Modifier Implementations
# =============================================================================

@register_modifier("stroke_weight", "Adjust stroke thickness")
class StrokeWeightModifier(BaseModifier):
    """Adjust stroke width of SVG elements."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply stroke weight modifier.

        Value mapping: 0.0 -> 0.5px, 0.5 -> 2px, 1.0 -> 10px
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> 0.5-10.0
        stroke_width = self.denormalize(value, 0.5, 10.0)

        # Find all elements with stroke
        for elem in svg_element.iter():
            if 'stroke' in elem.attrib and elem.attrib['stroke'] != 'none':
                elem.set('stroke-width', f"{stroke_width:.2f}")

        return svg_element


@register_modifier("fill_opacity", "Adjust fill transparency")
class FillOpacityModifier(BaseModifier):
    """Adjust fill opacity of SVG elements."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply fill opacity modifier.

        Value mapping: 0.0 -> 0.0 (transparent), 1.0 -> 1.0 (opaque)
        """
        self.validate_value(value)

        # Value is already normalized
        opacity = value

        # Find all elements with fill
        for elem in svg_element.iter():
            if 'fill' in elem.attrib and elem.attrib['fill'] != 'none':
                elem.set('fill-opacity', f"{opacity:.2f}")

        return svg_element


@register_modifier("hue_shift", "Rotate hue in HSL color space")
class HueShiftModifier(BaseModifier):
    """Shift hue of all colors in SVG."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply hue shift modifier.

        Value mapping: 0.0 -> -180°, 0.5 -> 0°, 1.0 -> +180°
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> -0.5 to +0.5 (hue shift)
        hue_shift = self.denormalize(value, -0.5, 0.5)

        # Adjust colors in fill and stroke
        for elem in svg_element.iter():
            if 'fill' in elem.attrib:
                elem.set('fill', adjust_hue(elem.attrib['fill'], hue_shift))
            if 'stroke' in elem.attrib:
                elem.set('stroke', adjust_hue(elem.attrib['stroke'], hue_shift))

        return svg_element


@register_modifier("scale", "Uniform scaling transformation")
class ScaleModifier(BaseModifier):
    """Scale SVG uniformly."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply scale modifier.

        Value mapping: 0.0 -> 0.5x, 0.5 -> 1.0x, 1.0 -> 2.0x
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> 0.5-2.0
        scale_factor = self.denormalize(value, 0.5, 2.0)

        # Add transform to root
        existing_transform = svg_element.get('transform', '')
        new_transform = f"scale({scale_factor:.3f})"

        if existing_transform:
            svg_element.set('transform', f"{existing_transform} {new_transform}")
        else:
            svg_element.set('transform', new_transform)

        return svg_element


@register_modifier("rotate", "Rotation in degrees")
class RotateModifier(BaseModifier):
    """Rotate SVG around center."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply rotate modifier.

        Value mapping: 0.0 -> 0°, 0.5 -> 180°, 1.0 -> 360°
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> 0-360 degrees
        angle = self.denormalize(value, 0, 360)

        # Get SVG dimensions for center calculation
        width = float(svg_element.get('width', '100'))
        height = float(svg_element.get('height', '100'))
        cx, cy = width / 2, height / 2

        # Add transform to root
        existing_transform = svg_element.get('transform', '')
        new_transform = f"rotate({angle:.1f} {cx:.1f} {cy:.1f})"

        if existing_transform:
            svg_element.set('transform', f"{existing_transform} {new_transform}")
        else:
            svg_element.set('transform', new_transform)

        return svg_element


@register_modifier("brightness", "Adjust lightness in HSL space")
class BrightnessModifier(BaseModifier):
    """Adjust brightness of all colors."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply brightness modifier.

        Value mapping: 0.0 -> -0.5 (darker), 0.5 -> 0.0, 1.0 -> +0.5 (lighter)
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> -0.5 to +0.5
        brightness_delta = self.denormalize(value, -0.5, 0.5)

        # Adjust colors in fill and stroke
        for elem in svg_element.iter():
            if 'fill' in elem.attrib:
                elem.set('fill', adjust_brightness(elem.attrib['fill'], brightness_delta))
            if 'stroke' in elem.attrib:
                elem.set('stroke', adjust_brightness(elem.attrib['stroke'], brightness_delta))

        return svg_element


@register_modifier("saturation", "Adjust color saturation")
class SaturationModifier(BaseModifier):
    """Adjust saturation of all colors."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply saturation modifier.

        Value mapping: 0.0 -> 0.0 (grayscale), 0.5 -> 1.0, 1.0 -> 2.0 (vibrant)
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> 0.0-2.0
        saturation_mult = self.denormalize(value, 0.0, 2.0)

        # Adjust colors in fill and stroke
        for elem in svg_element.iter():
            if 'fill' in elem.attrib:
                elem.set('fill', adjust_saturation(elem.attrib['fill'], saturation_mult))
            if 'stroke' in elem.attrib:
                elem.set('stroke', adjust_saturation(elem.attrib['stroke'], saturation_mult))

        return svg_element


@register_modifier("contrast", "Adjust value contrast")
class ContrastModifier(BaseModifier):
    """Adjust contrast of colors."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply contrast modifier.

        Value mapping: 0.0 -> low contrast, 0.5 -> normal, 1.0 -> high contrast
        Simple implementation: adjust brightness based on current lightness
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> 0.5-1.5 (contrast multiplier)
        contrast_mult = self.denormalize(value, 0.5, 1.5)

        # For simplicity, apply filter or adjust brightness
        # Here we'll add a filter for contrast
        # Create defs section if not exists
        defs = svg_element.find('.//{http://www.w3.org/2000/svg}defs')
        if defs is None:
            defs = etree.SubElement(svg_element, '{http://www.w3.org/2000/svg}defs')

        # Add filter
        filter_id = "contrast-filter"
        filter_elem = etree.SubElement(defs, '{http://www.w3.org/2000/svg}filter')
        filter_elem.set('id', filter_id)

        # ComponentTransfer for contrast
        component = etree.SubElement(filter_elem, '{http://www.w3.org/2000/svg}feComponentTransfer')
        for channel in ['R', 'G', 'B']:
            func = etree.SubElement(component, f'{{http://www.w3.org/2000/svg}}feFunc{channel}')
            func.set('type', 'linear')
            func.set('slope', f"{contrast_mult:.2f}")
            func.set('intercept', f"{(1 - contrast_mult) * 0.5:.2f}")

        # Apply filter to root
        svg_element.set('filter', f"url(#{filter_id})")

        return svg_element


@register_modifier("blur", "Add Gaussian blur effect")
class BlurModifier(BaseModifier):
    """Add Gaussian blur to SVG."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply blur modifier.

        Value mapping: 0.0 -> 0px blur, 0.5 -> 5px, 1.0 -> 10px
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> 0-10
        blur_amount = self.denormalize(value, 0, 10)

        if blur_amount == 0:
            return svg_element  # No blur

        # Create defs section if not exists
        defs = svg_element.find('.//{http://www.w3.org/2000/svg}defs')
        if defs is None:
            defs = etree.SubElement(svg_element, '{http://www.w3.org/2000/svg}defs')

        # Add blur filter
        filter_id = "blur-filter"
        filter_elem = etree.SubElement(defs, '{http://www.w3.org/2000/svg}filter')
        filter_elem.set('id', filter_id)

        blur = etree.SubElement(filter_elem, '{http://www.w3.org/2000/svg}feGaussianBlur')
        blur.set('stdDeviation', f"{blur_amount:.2f}")

        # Apply filter to root
        svg_element.set('filter', f"url(#{filter_id})")

        return svg_element


@register_modifier("x_offset", "Horizontal translation")
class XOffsetModifier(BaseModifier):
    """Translate SVG horizontally."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply x offset modifier.

        Value mapping: 0.0 -> -50px, 0.5 -> 0px, 1.0 -> +50px
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> -50 to +50
        x_offset = self.denormalize(value, -50, 50)

        # Add transform to root
        existing_transform = svg_element.get('transform', '')
        new_transform = f"translate({x_offset:.1f}, 0)"

        if existing_transform:
            svg_element.set('transform', f"{existing_transform} {new_transform}")
        else:
            svg_element.set('transform', new_transform)

        return svg_element


@register_modifier("y_offset", "Vertical translation")
class YOffsetModifier(BaseModifier):
    """Translate SVG vertically."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply y offset modifier.

        Value mapping: 0.0 -> -50px, 0.5 -> 0px, 1.0 -> +50px
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> -50 to +50
        y_offset = self.denormalize(value, -50, 50)

        # Add transform to root
        existing_transform = svg_element.get('transform', '')
        new_transform = f"translate(0, {y_offset:.1f})"

        if existing_transform:
            svg_element.set('transform', f"{existing_transform} {new_transform}")
        else:
            svg_element.set('transform', new_transform)

        return svg_element


@register_modifier("skew", "Skew transformation")
class SkewModifier(BaseModifier):
    """Skew SVG horizontally."""

    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply skew modifier.

        Value mapping: 0.0 -> -30°, 0.5 -> 0°, 1.0 -> +30°
        """
        self.validate_value(value)

        # Denormalize: 0.0-1.0 -> -30 to +30 degrees
        skew_angle = self.denormalize(value, -30, 30)

        # Add transform to root
        existing_transform = svg_element.get('transform', '')
        new_transform = f"skewX({skew_angle:.1f})"

        if existing_transform:
            svg_element.set('transform', f"{existing_transform} {new_transform}")
        else:
            svg_element.set('transform', new_transform)

        return svg_element
