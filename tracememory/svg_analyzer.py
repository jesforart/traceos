"""
TraceOS SVG Feature Analyzer
Extracts design features for Style DNA generation and analysis.

Built on top of the lxml parsing foundation.
"""

from lxml import etree
from typing import List, Dict, Tuple, Optional
import colorsys
import re
from collections import Counter


class SVGAnalyzer:
    """Extract design features from SVG documents."""

    def __init__(self, svg_string: str):
        """Initialize with SVG string."""
        self.svg_string = svg_string
        self.tree = self._parse_svg(svg_string)
        self.namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    def _parse_svg(self, svg_string: str) -> etree.Element:
        """Parse SVG string to lxml tree."""
        try:
            # Handle both string and bytes
            if isinstance(svg_string, str):
                svg_string = svg_string.encode('utf-8')
            return etree.fromstring(svg_string)
        except Exception as e:
            raise ValueError(f"Invalid SVG: {e}")

    # ==========================================
    # COLOR EXTRACTION
    # ==========================================

    def extract_colors(self) -> Dict[str, List[str]]:
        """
        Extract all colors from SVG.

        Note: Uses //*[@attribute] XPath syntax which works across namespaces.
        Tag-based queries (e.g., //svg:rect) require namespace specification.

        Returns:
            {
                'fills': ['#FF0000', '#00FF00', ...],
                'strokes': ['#000000', ...],
                'all': ['#FF0000', '#00FF00', '#000000', ...],
                'unique': ['#FF0000', '#00FF00', '#000000']
            }
        """
        fills = []
        strokes = []

        # Get all elements with fill attribute
        for element in self.tree.xpath('//*[@fill]'):
            fill = element.get('fill')
            if fill and fill not in ('none', 'transparent'):
                fills.append(self._normalize_color(fill))

        # Get all elements with stroke attribute
        for element in self.tree.xpath('//*[@stroke]'):
            stroke = element.get('stroke')
            if stroke and stroke not in ('none', 'transparent'):
                strokes.append(self._normalize_color(stroke))

        all_colors = fills + strokes
        unique_colors = list(set(all_colors))

        return {
            'fills': fills,
            'strokes': strokes,
            'all': all_colors,
            'unique': unique_colors,
            'count': len(unique_colors)
        }

    def get_color_palette(self, max_colors: int = 10) -> List[Tuple[str, int]]:
        """
        Get dominant color palette with usage counts.

        Args:
            max_colors: Maximum number of colors to return

        Returns:
            [('#FF0000', 5), ('#00FF00', 3), ...]
        """
        colors = self.extract_colors()['all']
        counter = Counter(colors)
        return counter.most_common(max_colors)

    def analyze_color_harmony(self) -> Dict:
        """
        Analyze color relationships and harmony.

        Returns:
            {
                'palette_type': 'monochromatic' | 'analogous' | 'complementary' | 'triadic',
                'avg_saturation': 0.65,
                'avg_brightness': 0.72,
                'contrast_ratio': 0.85
            }
        """
        colors = self.extract_colors()['unique']

        if not colors:
            return {'palette_type': 'none', 'avg_saturation': 0, 'avg_brightness': 0}

        # Convert to HSL
        hsl_colors = []
        for color in colors:
            rgb = self._hex_to_rgb(color)
            if rgb:
                hsl = colorsys.rgb_to_hls(*[c/255.0 for c in rgb])
                hsl_colors.append(hsl)

        if not hsl_colors:
            return {'palette_type': 'unknown', 'avg_saturation': 0, 'avg_brightness': 0}

        # Calculate averages
        avg_hue = sum(h for h, l, s in hsl_colors) / len(hsl_colors)
        avg_saturation = sum(s for h, l, s in hsl_colors) / len(hsl_colors)
        avg_brightness = sum(l for h, l, s in hsl_colors) / len(hsl_colors)

        # Determine palette type (simplified)
        hue_spread = max(h for h, l, s in hsl_colors) - min(h for h, l, s in hsl_colors)

        if hue_spread < 0.1:
            palette_type = 'monochromatic'
        elif hue_spread < 0.25:
            palette_type = 'analogous'
        elif 0.4 < hue_spread < 0.6:
            palette_type = 'complementary'
        else:
            palette_type = 'triadic'

        return {
            'palette_type': palette_type,
            'avg_saturation': round(avg_saturation, 2),
            'avg_brightness': round(avg_brightness, 2),
            'hue_spread': round(hue_spread, 2)
        }

    def _normalize_color(self, color: str) -> str:
        """Normalize color to hex format."""
        # Handle rgb(r,g,b) format
        if color.startswith('rgb'):
            match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
            if match:
                r, g, b = [int(x) for x in match.groups()]
                return f'#{r:02x}{g:02x}{b:02x}'

        # Already hex
        if color.startswith('#'):
            return color.upper()

        # Named colors - return as-is for now
        return color

    def _hex_to_rgb(self, hex_color: str) -> Optional[Tuple[int, int, int]]:
        """Convert hex color to RGB tuple."""
        if not hex_color.startswith('#'):
            return None

        hex_color = hex_color.lstrip('#')

        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])

        if len(hex_color) != 6:
            return None

        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            return None

    # ==========================================
    # TYPOGRAPHY EXTRACTION
    # ==========================================

    def extract_typography(self) -> Dict:
        """
        Extract typography information.

        Returns:
            {
                'font_families': ['Arial', 'Helvetica', ...],
                'font_sizes': [12, 14, 16, 24, ...],
                'font_weights': [400, 700, ...],
                'text_elements': [
                    {'text': 'Hello', 'font': 'Arial', 'size': 16, 'weight': 400},
                    ...
                ]
            }
        """
        text_elements = []
        font_families = []
        font_sizes = []
        font_weights = []

        # Find all text elements
        for text_elem in self.tree.xpath('//svg:text', namespaces=self.namespaces):
            text_data = {
                'text': text_elem.text or '',
                'font_family': text_elem.get('font-family', 'inherit'),
                'font_size': text_elem.get('font-size', 'inherit'),
                'font_weight': text_elem.get('font-weight', '400'),
                'fill': text_elem.get('fill', '#000000')
            }

            text_elements.append(text_data)

            if text_data['font_family'] != 'inherit':
                font_families.append(text_data['font_family'])

            if text_data['font_size'] != 'inherit':
                # Extract numeric size
                size_match = re.search(r'(\d+)', text_data['font_size'])
                if size_match:
                    font_sizes.append(int(size_match.group(1)))

            if text_data['font_weight'] != 'inherit':
                weight_match = re.search(r'(\d+)', str(text_data['font_weight']))
                if weight_match:
                    font_weights.append(int(weight_match.group(1)))

        return {
            'font_families': list(set(font_families)),
            'font_sizes': sorted(list(set(font_sizes))),
            'font_weights': sorted(list(set(font_weights))),
            'text_elements': text_elements,
            'text_count': len(text_elements)
        }

    def calculate_type_scale(self) -> Dict:
        """
        Calculate typographic scale ratios.

        Returns:
            {
                'base_size': 16,
                'scale_ratio': 1.5,
                'sizes': [12, 16, 24, 36]
            }
        """
        typography = self.extract_typography()
        sizes = typography['font_sizes']

        if len(sizes) < 2:
            return {'base_size': sizes[0] if sizes else 16, 'scale_ratio': 1.0, 'sizes': sizes}

        # Assume smallest is base
        base_size = min(sizes)

        # Calculate average ratio between consecutive sizes
        ratios = []
        sorted_sizes = sorted(sizes)
        for i in range(len(sorted_sizes) - 1):
            ratio = sorted_sizes[i + 1] / sorted_sizes[i]
            ratios.append(ratio)

        avg_ratio = sum(ratios) / len(ratios) if ratios else 1.0

        return {
            'base_size': base_size,
            'scale_ratio': round(avg_ratio, 2),
            'sizes': sorted_sizes
        }

    # ==========================================
    # LAYOUT & SPACING EXTRACTION
    # ==========================================

    def extract_spacing(self) -> Dict:
        """
        Extract spacing and layout information.

        Returns:
            {
                'element_count': 42,
                'avg_spacing': 16.5,
                'bounding_box': {'width': 800, 'height': 600},
                'density': 0.65
            }
        """
        # Get SVG dimensions
        width = self._get_numeric_attr(self.tree, 'width', 800)
        height = self._get_numeric_attr(self.tree, 'height', 600)

        # Count all visual elements
        elements = self.tree.xpath('//*[name()="rect" or name()="circle" or name()="ellipse" or name()="path" or name()="polygon" or name()="text"]')
        element_count = len(elements)

        # Calculate density (elements per 10000 sq px)
        area = width * height
        density = (element_count / area) * 10000 if area > 0 else 0

        # Estimate average spacing (simplified)
        if element_count > 1:
            avg_spacing = ((width + height) / 2) / element_count
        else:
            avg_spacing = 0

        return {
            'element_count': element_count,
            'canvas_width': width,
            'canvas_height': height,
            'avg_spacing': round(avg_spacing, 2),
            'density': round(density, 2)
        }

    def get_bounding_boxes(self) -> Dict[str, Dict]:
        """
        Get bounding boxes for all elements with IDs.

        Returns:
            {
                'rect1': {'x': 10, 'y': 20, 'width': 100, 'height': 50},
                'circle1': {'cx': 150, 'cy': 150, 'r': 30},
                ...
            }
        """
        bboxes = {}

        for element in self.tree.xpath('//*[@id]'):
            elem_id = element.get('id')
            bbox = {}

            # Rect
            if element.tag.endswith('rect'):
                bbox = {
                    'x': self._get_numeric_attr(element, 'x', 0),
                    'y': self._get_numeric_attr(element, 'y', 0),
                    'width': self._get_numeric_attr(element, 'width', 0),
                    'height': self._get_numeric_attr(element, 'height', 0)
                }

            # Circle
            elif element.tag.endswith('circle'):
                bbox = {
                    'cx': self._get_numeric_attr(element, 'cx', 0),
                    'cy': self._get_numeric_attr(element, 'cy', 0),
                    'r': self._get_numeric_attr(element, 'r', 0)
                }

            # Add more shape types as needed

            if bbox:
                bboxes[elem_id] = bbox

        return bboxes

    # ==========================================
    # SHAPE ANALYSIS
    # ==========================================

    def analyze_shapes(self) -> Dict:
        """
        Analyze shape usage and complexity.

        Returns:
            {
                'rectangles': 5,
                'circles': 3,
                'paths': 2,
                'total_shapes': 10,
                'avg_border_radius': 8.5,
                'shape_distribution': {'rect': 0.5, 'circle': 0.3, 'path': 0.2}
            }
        """
        shape_counts = {
            'rectangles': len(self.tree.xpath('//svg:rect', namespaces=self.namespaces)),
            'circles': len(self.tree.xpath('//svg:circle', namespaces=self.namespaces)),
            'ellipses': len(self.tree.xpath('//svg:ellipse', namespaces=self.namespaces)),
            'paths': len(self.tree.xpath('//svg:path', namespaces=self.namespaces)),
            'polygons': len(self.tree.xpath('//svg:polygon', namespaces=self.namespaces)),
            'lines': len(self.tree.xpath('//svg:line', namespaces=self.namespaces))
        }

        total = sum(shape_counts.values())

        # Calculate distribution
        distribution = {k: v/total if total > 0 else 0 for k, v in shape_counts.items()}

        # Extract border radius from rects
        border_radii = []
        for rect in self.tree.xpath('//svg:rect[@rx]', namespaces=self.namespaces):
            rx = self._get_numeric_attr(rect, 'rx', 0)
            if rx > 0:
                border_radii.append(rx)

        avg_border_radius = sum(border_radii) / len(border_radii) if border_radii else 0

        return {
            **shape_counts,
            'total_shapes': total,
            'avg_border_radius': round(avg_border_radius, 2),
            'shape_distribution': {k: round(v, 2) for k, v in distribution.items()}
        }

    def extract_border_radius(self) -> List[float]:
        """Extract all border radius values (rx, ry)."""
        radii = []

        for rect in self.tree.xpath('//svg:rect', namespaces=self.namespaces):
            rx = self._get_numeric_attr(rect, 'rx', 0)
            ry = self._get_numeric_attr(rect, 'ry', 0)

            if rx > 0:
                radii.append(rx)
            if ry > 0 and ry != rx:
                radii.append(ry)

        return radii

    # ==========================================
    # COMPLETE FEATURE SET
    # ==========================================

    def extract_all_features(self) -> Dict:
        """
        Extract complete feature set for Style DNA generation.

        Returns comprehensive dictionary with all design features.
        """
        return {
            'colors': self.extract_colors(),
            'color_harmony': self.analyze_color_harmony(),
            'typography': self.extract_typography(),
            'type_scale': self.calculate_type_scale(),
            'spacing': self.extract_spacing(),
            'shapes': self.analyze_shapes(),
            'bounding_boxes': self.get_bounding_boxes()
        }

    # ==========================================
    # UTILITY FUNCTIONS
    # ==========================================

    def _get_numeric_attr(self, element, attr_name: str, default: float = 0) -> float:
        """Extract numeric value from attribute."""
        value = element.get(attr_name, str(default))

        # Extract first number found
        match = re.search(r'(\d+\.?\d*)', str(value))
        if match:
            return float(match.group(1))

        return default


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def extract_colors(svg_string: str) -> Dict[str, List[str]]:
    """Extract colors from SVG string."""
    analyzer = SVGAnalyzer(svg_string)
    return analyzer.extract_colors()


def extract_typography(svg_string: str) -> Dict:
    """Extract typography from SVG string."""
    analyzer = SVGAnalyzer(svg_string)
    return analyzer.extract_typography()


def extract_spacing(svg_string: str) -> Dict:
    """Extract spacing from SVG string."""
    analyzer = SVGAnalyzer(svg_string)
    return analyzer.extract_spacing()


def analyze_shapes(svg_string: str) -> Dict:
    """Analyze shapes in SVG string."""
    analyzer = SVGAnalyzer(svg_string)
    return analyzer.analyze_shapes()


def extract_all_features(svg_string: str) -> Dict:
    """Extract all features from SVG string."""
    analyzer = SVGAnalyzer(svg_string)
    return analyzer.extract_all_features()
