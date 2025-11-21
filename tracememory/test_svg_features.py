"""
Tests for SVG Feature Extraction and CRUD operations.
"""

import pytest
from svg_analyzer import SVGAnalyzer, extract_all_features
from svg_crud import SVGCRUD, ElementNotFoundError


# Sample SVG for testing
SAMPLE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
  <rect id="rect1" x="10" y="10" width="100" height="100" fill="#FF0000" rx="5"/>
  <circle id="circle1" cx="200" cy="200" r="50" fill="#00FF00"/>
  <text id="text1" x="300" y="300" font-family="Arial" font-size="24" font-weight="700" fill="#0000FF">Hello World</text>
  <rect id="rect2" x="400" y="400" width="150" height="75" fill="#FF00FF" rx="10"/>
</svg>
"""


class TestSVGAnalyzer:
    """Test SVG feature extraction."""

    def test_extract_colors(self):
        """Test color extraction."""
        analyzer = SVGAnalyzer(SAMPLE_SVG)
        colors = analyzer.extract_colors()

        assert 'fills' in colors
        assert 'strokes' in colors
        assert 'unique' in colors
        assert len(colors['unique']) >= 4  # At least 4 different colors
        assert '#FF0000' in colors['all']

    def test_color_palette(self):
        """Test color palette generation."""
        analyzer = SVGAnalyzer(SAMPLE_SVG)
        palette = analyzer.get_color_palette(max_colors=5)

        assert isinstance(palette, list)
        assert len(palette) <= 5
        assert all(isinstance(item, tuple) and len(item) == 2 for item in palette)

    def test_extract_typography(self):
        """Test typography extraction."""
        analyzer = SVGAnalyzer(SAMPLE_SVG)
        typography = analyzer.extract_typography()

        assert 'font_families' in typography
        assert 'font_sizes' in typography
        assert 'font_weights' in typography
        assert 'text_elements' in typography

        assert 'Arial' in typography['font_families']
        assert 24 in typography['font_sizes']
        assert 700 in typography['font_weights']

    def test_extract_spacing(self):
        """Test spacing extraction."""
        analyzer = SVGAnalyzer(SAMPLE_SVG)
        spacing = analyzer.extract_spacing()

        assert 'element_count' in spacing
        assert 'canvas_width' in spacing
        assert 'canvas_height' in spacing
        assert spacing['canvas_width'] == 800
        assert spacing['canvas_height'] == 600

    def test_analyze_shapes(self):
        """Test shape analysis."""
        analyzer = SVGAnalyzer(SAMPLE_SVG)
        shapes = analyzer.analyze_shapes()

        assert 'rectangles' in shapes
        assert 'circles' in shapes
        assert 'total_shapes' in shapes
        assert shapes['rectangles'] == 2  # rect1 and rect2
        assert shapes['circles'] == 1

    def test_extract_all_features(self):
        """Test complete feature extraction."""
        features = extract_all_features(SAMPLE_SVG)

        assert 'colors' in features
        assert 'typography' in features
        assert 'spacing' in features
        assert 'shapes' in features


class TestSVGCRUD:
    """Test SVG CRUD operations."""

    def test_get_element_by_id(self):
        """Test getting element by ID."""
        crud = SVGCRUD(SAMPLE_SVG)
        element = crud.get_element_by_id('rect1')

        assert element is not None
        assert element.get('id') == 'rect1'
        assert element.get('fill') == '#FF0000'

    def test_get_element_attributes(self):
        """Test getting element attributes."""
        crud = SVGCRUD(SAMPLE_SVG)
        attrs = crud.get_element_attributes('circle1')

        assert 'id' in attrs
        assert 'cx' in attrs
        assert 'cy' in attrs
        assert 'r' in attrs
        assert attrs['fill'] == '#00FF00'

    def test_update_element(self):
        """Test updating element."""
        crud = SVGCRUD(SAMPLE_SVG)
        updated_svg = crud.update_element('rect1', {'fill': '#FFFF00', 'rx': '15'})

        # Parse updated SVG
        crud2 = SVGCRUD(updated_svg)
        attrs = crud2.get_element_attributes('rect1')

        assert attrs['fill'] == '#FFFF00'
        assert attrs['rx'] == '15'

    def test_create_element(self):
        """Test creating element."""
        crud = SVGCRUD(SAMPLE_SVG)
        updated_svg = crud.create_element('ellipse', {
            'id': 'ellipse1',
            'cx': '500',
            'cy': '500',
            'rx': '100',
            'ry': '50',
            'fill': '#AAAAAA'
        })

        # Parse updated SVG
        crud2 = SVGCRUD(updated_svg)
        element = crud2.get_element_by_id('ellipse1')

        assert element is not None
        assert element.get('cx') == '500'

    def test_delete_element(self):
        """Test deleting element."""
        crud = SVGCRUD(SAMPLE_SVG)
        updated_svg = crud.delete_element('rect2')

        # Parse updated SVG
        crud2 = SVGCRUD(updated_svg)
        element = crud2.get_element_by_id('rect2')

        assert element is None

    def test_clone_element(self):
        """Test cloning element."""
        crud = SVGCRUD(SAMPLE_SVG)
        updated_svg = crud.clone_element('circle1', 'circle2', 'translate(100, 100)')

        # Parse updated SVG
        crud2 = SVGCRUD(updated_svg)

        # Both should exist
        original = crud2.get_element_by_id('circle1')
        cloned = crud2.get_element_by_id('circle2')

        assert original is not None
        assert cloned is not None
        assert cloned.get('transform') == 'translate(100, 100)'

    def test_element_not_found_error(self):
        """Test error handling for missing element."""
        crud = SVGCRUD(SAMPLE_SVG)

        with pytest.raises(ElementNotFoundError):
            crud.get_element_attributes('nonexistent')

        with pytest.raises(ElementNotFoundError):
            crud.update_element('nonexistent', {'fill': '#000000'})


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
