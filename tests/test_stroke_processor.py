import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../tracememory'))

from drawing.models import Stroke, Point
from drawing.stroke_processor import StrokeProcessor

def test_stroke_smoothing():
    """Test stroke smoothing."""
    points = [
        Point(x=0, y=0, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0),
        Point(x=10, y=10, pressure=0.6, tilt_x=0, tilt_y=0, timestamp=10),
        Point(x=20, y=20, pressure=0.7, tilt_x=0, tilt_y=0, timestamp=20),
        Point(x=30, y=30, pressure=0.8, tilt_x=0, tilt_y=0, timestamp=30),
        Point(x=40, y=40, pressure=0.9, tilt_x=0, tilt_y=0, timestamp=40),
    ]

    stroke = Stroke(
        id="test_1",
        points=points,
        tool="pen",
        color="#000000",
        width=3.0,
        layer_id="layer_1",
        created_at=0
    )

    processor = StrokeProcessor(smoothing_factor=0.3)
    smoothed = processor.smooth_stroke(stroke)

    assert len(smoothed.points) == len(points)
    assert smoothed.points[0].x == points[0].x
    assert smoothed.points[0].y == points[0].y

def test_metrics_calculation():
    """Test stroke metrics calculation."""
    points = [
        Point(x=0, y=0, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0),
        Point(x=10, y=0, pressure=0.7, tilt_x=0, tilt_y=0, timestamp=10),
        Point(x=20, y=0, pressure=0.9, tilt_x=0, tilt_y=0, timestamp=20),
    ]

    stroke = Stroke(
        id="test_2",
        points=points,
        tool="pen",
        color="#000000",
        width=3.0,
        layer_id="layer_1",
        created_at=0
    )

    processor = StrokeProcessor()
    metrics = processor.calculate_metrics(stroke)

    assert metrics.avg_pressure > 0
    assert metrics.length > 0
    assert metrics.avg_speed > 0
    assert 0 <= metrics.smoothness <= 1

def test_empty_stroke():
    """Test handling of empty stroke."""
    stroke = Stroke(
        id="test_empty",
        points=[],
        tool="pen",
        color="#000000",
        width=3.0,
        layer_id="layer_1",
        created_at=0
    )

    processor = StrokeProcessor()
    metrics = processor.calculate_metrics(stroke)

    assert metrics.avg_pressure == 0
    assert metrics.length == 0
    assert metrics.avg_speed == 0

def test_single_point_stroke():
    """Test handling of single point stroke."""
    points = [Point(x=10, y=10, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)]

    stroke = Stroke(
        id="test_single",
        points=points,
        tool="pen",
        color="#000000",
        width=3.0,
        layer_id="layer_1",
        created_at=0
    )

    processor = StrokeProcessor()
    metrics = processor.calculate_metrics(stroke)

    assert metrics.avg_pressure == 0.5
    assert metrics.length == 0
    assert metrics.bounding_box['min_x'] == 10
    assert metrics.bounding_box['min_y'] == 10

def test_process_stroke():
    """Test complete stroke processing."""
    points = [
        Point(x=0, y=0, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0),
        Point(x=10, y=10, pressure=0.7, tilt_x=0, tilt_y=0, timestamp=10),
        Point(x=20, y=20, pressure=0.9, tilt_x=0, tilt_y=0, timestamp=20),
    ]

    stroke = Stroke(
        id="test_process",
        points=points,
        tool="pen",
        color="#000000",
        width=3.0,
        layer_id="layer_1",
        created_at=0
    )

    processor = StrokeProcessor()
    processed = processor.process_stroke(stroke)

    assert processed.stroke.id == "test_process"
    assert len(processed.smoothed_points) == len(points)
    assert processed.metrics.avg_pressure > 0
    assert processed.metrics.length > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
