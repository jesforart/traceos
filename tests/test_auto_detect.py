import pytest
from tracememory.drawing.models import Stroke, Point
from tracememory.drawing.auto_detector import AutoDetector

def test_face_detection_basic():
    """Test basic face element detection."""
    # Create test strokes in different regions
    strokes = [
        # Top stroke (eyebrow region)
        Stroke(
            id="stroke_1",
            points=[Point(x=10, y=10, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
        # Middle stroke (nose region)
        Stroke(
            id="stroke_2",
            points=[Point(x=10, y=50, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
        # Bottom stroke (mouth region)
        Stroke(
            id="stroke_3",
            points=[Point(x=10, y=80, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
    ]

    detector = AutoDetector()
    elements = detector.detect_face_elements(strokes)

    # Should detect at least 2 elements
    assert len(elements) >= 2

    # Check labels are assigned
    labels = [e.label for e in elements]
    assert any('eyebrow' in label or 'nose' in label or 'mouth' in label for label in labels)

    # Check confidence scores
    for element in elements:
        assert 0.0 <= element.confidence <= 1.0
        assert element.auto_detected == True


def test_face_detection_insufficient_strokes():
    """Test detection with too few strokes."""
    strokes = [
        Stroke(
            id="stroke_1",
            points=[Point(x=10, y=10, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
    ]

    detector = AutoDetector()
    elements = detector.detect_face_elements(strokes)

    # Should return empty list for insufficient strokes
    assert len(elements) == 0


def test_face_detection_left_right_assignment():
    """Test left/right eye and eyebrow assignment."""
    strokes = [
        # Left eyebrow (top left)
        Stroke(
            id="stroke_1",
            points=[Point(x=30, y=20, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
        # Right eyebrow (top right)
        Stroke(
            id="stroke_2",
            points=[Point(x=70, y=20, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
        # Left eye (middle left)
        Stroke(
            id="stroke_3",
            points=[Point(x=30, y=40, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
        # Right eye (middle right)
        Stroke(
            id="stroke_4",
            points=[Point(x=70, y=40, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
    ]

    detector = AutoDetector()
    elements = detector.detect_face_elements(strokes)

    labels = [e.label for e in elements]

    # Should detect left and right elements
    assert 'left_eyebrow' in labels or 'left_eye' in labels
    assert 'right_eyebrow' in labels or 'right_eye' in labels


def test_bounding_box_calculation():
    """Test bounding box is calculated correctly."""
    strokes = [
        Stroke(
            id="stroke_1",
            points=[
                Point(x=10, y=10, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0),
                Point(x=20, y=20, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=1),
                Point(x=30, y=15, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=2),
            ],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
        Stroke(
            id="stroke_2",
            points=[Point(x=50, y=50, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
        Stroke(
            id="stroke_3",
            points=[Point(x=50, y=80, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
    ]

    detector = AutoDetector()
    elements = detector.detect_face_elements(strokes)

    # Each element should have valid bounding box
    for element in elements:
        bbox = element.bounding_box
        assert bbox.min_x <= bbox.max_x
        assert bbox.min_y <= bbox.max_y
        assert bbox.min_x >= 0
        assert bbox.min_y >= 0


def test_confidence_filtering():
    """Test that low confidence elements are filtered."""
    detector = AutoDetector()

    # Set high min_confidence
    detector.min_confidence = 0.9

    strokes = [
        Stroke(
            id="stroke_1",
            points=[Point(x=10, y=10, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
        Stroke(
            id="stroke_2",
            points=[Point(x=10, y=50, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
        Stroke(
            id="stroke_3",
            points=[Point(x=10, y=80, pressure=0.5, tilt_x=0, tilt_y=0, timestamp=0)],
            tool="pen",
            color="#000",
            width=2.0,
            layer_id="layer_1",
            created_at=0
        ),
    ]

    elements = detector.detect_face_elements(strokes)

    # Should filter out elements with confidence < 0.9
    # (most heuristic confidences are 0.5-0.8)
    assert len(elements) <= 1  # Only nose might pass with 0.8
