import numpy as np
from typing import List
from .models import Stroke, Point, StrokeMetrics, ProcessedStroke

class StrokeProcessor:
    """
    Process incoming strokes from frontend.
    """

    def __init__(self, smoothing_factor: float = 0.3):
        self.smoothing_factor = smoothing_factor

    def process_stroke(self, stroke: Stroke) -> ProcessedStroke:
        """Process raw stroke data."""
        smoothed = self.smooth_stroke(stroke)
        metrics = self.calculate_metrics(stroke)

        return ProcessedStroke(
            stroke=stroke,
            metrics=metrics,
            smoothed_points=smoothed.points
        )

    def smooth_stroke(self, stroke: Stroke) -> Stroke:
        """Apply exponential moving average smoothing."""
        if len(stroke.points) < 3:
            return stroke

        smoothed_points = [stroke.points[0]]

        for i in range(1, len(stroke.points)):
            prev = smoothed_points[-1]
            curr = stroke.points[i]

            smoothed_x = prev.x * (1 - self.smoothing_factor) + curr.x * self.smoothing_factor
            smoothed_y = prev.y * (1 - self.smoothing_factor) + curr.y * self.smoothing_factor

            smoothed_points.append(Point(
                x=smoothed_x,
                y=smoothed_y,
                pressure=curr.pressure,
                tilt_x=curr.tilt_x,
                tilt_y=curr.tilt_y,
                timestamp=curr.timestamp
            ))

        return Stroke(
            **stroke.dict(exclude={'points'}),
            points=smoothed_points
        )

    def calculate_metrics(self, stroke: Stroke) -> StrokeMetrics:
        """Calculate stroke metrics."""
        points = stroke.points

        if not points:
            return StrokeMetrics(
                avg_pressure=0,
                pressure_variance=0,
                avg_speed=0,
                length=0,
                smoothness=0,
                bounding_box={'min_x': 0, 'min_y': 0, 'max_x': 0, 'max_y': 0}
            )

        pressures = [p.pressure for p in points]
        avg_pressure = np.mean(pressures)
        pressure_variance = np.var(pressures)

        length = 0.0
        total_time = 0

        for i in range(1, len(points)):
            dx = points[i].x - points[i-1].x
            dy = points[i].y - points[i-1].y
            segment_length = np.sqrt(dx**2 + dy**2)
            length += segment_length

            dt = points[i].timestamp - points[i-1].timestamp
            total_time += dt

        avg_speed = (length / total_time * 1000) if total_time > 0 else 0

        direction_changes = 0
        for i in range(2, len(points)):
            angle1 = np.arctan2(
                points[i-1].y - points[i-2].y,
                points[i-1].x - points[i-2].x
            )
            angle2 = np.arctan2(
                points[i].y - points[i-1].y,
                points[i].x - points[i-1].x
            )
            angle_diff = abs(angle2 - angle1)
            if angle_diff > np.pi / 4:
                direction_changes += 1

        smoothness = 1.0 - (direction_changes / len(points)) if len(points) > 0 else 1.0

        xs = [p.x for p in points]
        ys = [p.y for p in points]

        return StrokeMetrics(
            avg_pressure=float(avg_pressure),
            pressure_variance=float(pressure_variance),
            avg_speed=float(avg_speed),
            length=float(length),
            smoothness=float(smoothness),
            bounding_box={
                "min_x": min(xs),
                "min_y": min(ys),
                "max_x": max(xs),
                "max_y": max(ys)
            }
        )
