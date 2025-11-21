import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
from .models import Stroke, Point
from .semantic_models import SemanticElement, BoundingBox

class AutoDetector:
    """
    Auto-detect semantic elements using heuristics.

    Simple region-based detection for Day 2.
    Can be enhanced with ML later.
    """

    def __init__(self):
        self.min_confidence = 0.5

    def detect_face_elements(
        self,
        strokes: List[Stroke]
    ) -> List[SemanticElement]:
        """
        Auto-detect facial elements from strokes.

        Uses simple heuristics:
        - Divide face into horizontal regions
        - Assign strokes based on position
        - Calculate confidence based on consistency
        """
        if len(strokes) < 3:
            return []  # Need at least 3 strokes

        # Calculate overall bounding box
        all_points = []
        for stroke in strokes:
            all_points.extend([(p.x, p.y) for p in stroke.points])

        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        height = max_y - min_y
        width = max_x - min_x
        center_x = (min_x + max_x) / 2

        # Define regions
        regions = self._define_face_regions(min_x, max_x, min_y, max_y)

        # Assign strokes to regions
        detected_elements = []

        for stroke in strokes:
            stroke_center = self._get_stroke_center(stroke)
            assigned_region = self._assign_to_region(stroke_center, regions, center_x)

            if assigned_region:
                label, confidence = assigned_region

                # Check if element already exists for this label
                existing = next(
                    (e for e in detected_elements if e.label == label),
                    None
                )

                if existing:
                    # Add to existing element
                    existing.stroke_ids.append(stroke.id)
                    existing.bounding_box = self._update_bounding_box(
                        existing.bounding_box,
                        stroke
                    )
                else:
                    # Create new element
                    element = SemanticElement(
                        id=f"auto_{label}_{len(detected_elements)}",
                        label=label,
                        stroke_ids=[stroke.id],
                        bounding_box=self._get_stroke_bounding_box(stroke),
                        confidence=confidence,
                        auto_detected=True,
                        created_at=int(datetime.now().timestamp() * 1000)
                    )
                    detected_elements.append(element)

        # Filter by confidence
        return [e for e in detected_elements if e.confidence >= self.min_confidence]

    def _define_face_regions(
        self,
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float
    ) -> Dict[str, Tuple[float, float, float, float]]:
        """
        Define facial regions as (min_x, max_x, min_y, max_y).
        """
        height = max_y - min_y
        width = max_x - min_x

        return {
            "eyebrow_region": (min_x, max_x, min_y, min_y + height * 0.25),
            "eye_region": (min_x, max_x, min_y + height * 0.25, min_y + height * 0.45),
            "nose_region": (min_x, max_x, min_y + height * 0.45, min_y + height * 0.65),
            "mouth_region": (min_x, max_x, min_y + height * 0.65, min_y + height * 0.85),
            "jaw_region": (min_x, max_x, min_y + height * 0.85, max_y)
        }

    def _get_stroke_center(self, stroke: Stroke) -> Tuple[float, float]:
        """Calculate center point of stroke."""
        xs = [p.x for p in stroke.points]
        ys = [p.y for p in stroke.points]
        return (np.mean(xs), np.mean(ys))

    def _assign_to_region(
        self,
        point: Tuple[float, float],
        regions: Dict,
        center_x: float
    ) -> Tuple[str, float]:
        """
        Assign point to facial region.

        Returns (label, confidence).
        """
        x, y = point

        for region_name, (min_x, max_x, min_y, max_y) in regions.items():
            if min_x <= x <= max_x and min_y <= y <= max_y:
                # Determine specific element
                if region_name == "eyebrow_region":
                    label = "left_eyebrow" if x < center_x else "right_eyebrow"
                    confidence = 0.7
                elif region_name == "eye_region":
                    label = "left_eye" if x < center_x else "right_eye"
                    confidence = 0.75
                elif region_name == "nose_region":
                    label = "nose"
                    confidence = 0.8
                elif region_name == "mouth_region":
                    label = "mouth"
                    confidence = 0.75
                elif region_name == "jaw_region":
                    label = "jaw"
                    confidence = 0.6
                else:
                    label = "outline"
                    confidence = 0.5

                return (label, confidence)

        return ("outline", 0.5)

    def _get_stroke_bounding_box(self, stroke: Stroke) -> BoundingBox:
        """Get bounding box for single stroke."""
        xs = [p.x for p in stroke.points]
        ys = [p.y for p in stroke.points]

        return BoundingBox(
            min_x=min(xs),
            min_y=min(ys),
            max_x=max(xs),
            max_y=max(ys)
        )

    def _update_bounding_box(
        self,
        bbox: BoundingBox,
        stroke: Stroke
    ) -> BoundingBox:
        """Update bounding box to include stroke."""
        xs = [p.x for p in stroke.points]
        ys = [p.y for p in stroke.points]

        return BoundingBox(
            min_x=min(bbox.min_x, min(xs)),
            min_y=min(bbox.min_y, min(ys)),
            max_x=max(bbox.max_x, max(xs)),
            max_y=max(bbox.max_y, max(ys))
        )
