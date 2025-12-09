"""
Motion Engine - Trajectory Generation

Generates biologically plausible stroke trajectories
based on MotionParams derived from organism state.

Uses:
- Linear interpolation with jitter for natural variation
- Bezier smoothing for flow state
- Pressure curves based on velocity

@provenance traceos_hands_v1
@organ somatic
"""

import logging
import math
import random
from typing import List, Tuple

from .schemas import StrokePoint, MotionParams

logger = logging.getLogger(__name__)


class MotionEngine:
    """
    Generates stroke trajectories from motion parameters.

    This is the low-level engine that produces point sequences.
    The StrokePlanner handles organism state → MotionParams translation.
    """

    def __init__(self, seed: int = None):
        """
        Initialize the motion engine.

        Args:
            seed: Random seed for reproducible jitter (None = random)
        """
        if seed is not None:
            random.seed(seed)
        logger.info("MotionEngine initialized")

    def generate_trajectory(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        params: MotionParams
    ) -> List[StrokePoint]:
        """
        Generate a trajectory from start to end with given parameters.

        Args:
            start: (x, y) start position
            end: (x, y) end position
            params: Motion parameters controlling generation

        Returns:
            List of StrokePoints forming the trajectory
        """
        # Calculate stroke length
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.001:
            # Degenerate case: start == end (should be caught earlier)
            logger.warning("Degenerate stroke: start == end")
            return [StrokePoint(
                x=start[0],
                y=start[1],
                pressure=params.pressure_base,
                velocity=0.0,
                time=0.0
            )]

        # Calculate number of points based on distance and interval
        # Longer strokes get more points
        base_points = max(5, int(distance / 10))  # ~1 point per 10 pixels
        num_points = base_points

        logger.debug(f"Generating {num_points} points for distance {distance:.1f}")

        points: List[StrokePoint] = []
        time_accumulator = 0.0

        for i in range(num_points):
            # Parameter t goes from 0 to 1
            t = i / max(1, num_points - 1)

            # Base interpolation
            base_x = start[0] + t * dx
            base_y = start[1] + t * dy

            # Add jitter (tremor)
            jitter_x = 0.0
            jitter_y = 0.0
            if params.jitter_amount > 0 and 0 < t < 1:  # No jitter at endpoints
                jitter_x = random.gauss(0, params.jitter_amount)
                jitter_y = random.gauss(0, params.jitter_amount)

            # Apply smoothing (reduce jitter based on smoothing factor)
            smooth_factor = params.smoothing_factor
            jitter_x *= (1.0 - smooth_factor * 0.8)
            jitter_y *= (1.0 - smooth_factor * 0.8)

            x = base_x + jitter_x
            y = base_y + jitter_y

            # Velocity: faster in the middle, slower at ends (bell curve)
            velocity_curve = math.sin(t * math.pi)  # 0 at ends, 1 in middle
            velocity = params.velocity_base * (0.5 + 0.5 * velocity_curve)

            # Pressure: inverse of velocity (press harder when slower)
            # Also add slight arc (more pressure in middle)
            pressure_curve = 0.3 * math.sin(t * math.pi)
            pressure = params.pressure_base * params.pressure_gain
            pressure = min(1.0, pressure + pressure_curve)
            pressure = max(0.1, pressure * (1.0 - 0.2 * velocity_curve))

            # Time: based on interval and velocity
            if i > 0:
                time_accumulator += params.point_interval_ms / velocity

            point = StrokePoint(
                x=x,
                y=y,
                pressure=pressure,
                velocity=velocity,
                time=time_accumulator
            )
            points.append(point)

        logger.debug(f"Generated trajectory: {len(points)} points, {time_accumulator:.1f}ms duration")
        return points

    def apply_smoothing(
        self,
        points: List[StrokePoint],
        factor: float = 0.5
    ) -> List[StrokePoint]:
        """
        Apply additional smoothing to an existing trajectory.

        Uses simple moving average.

        Args:
            points: Input trajectory
            factor: Smoothing strength (0=none, 1=max)

        Returns:
            Smoothed trajectory
        """
        if len(points) < 3 or factor <= 0:
            return points

        smoothed = []
        window_size = max(2, int(factor * 5))

        for i, point in enumerate(points):
            if i == 0 or i == len(points) - 1:
                # Keep endpoints exact
                smoothed.append(point)
                continue

            # Average with neighbors
            start_idx = max(0, i - window_size)
            end_idx = min(len(points), i + window_size + 1)
            neighbors = points[start_idx:end_idx]

            avg_x = sum(p.x for p in neighbors) / len(neighbors)
            avg_y = sum(p.y for p in neighbors) / len(neighbors)

            # Blend original with average based on factor
            blend_x = point.x * (1 - factor) + avg_x * factor
            blend_y = point.y * (1 - factor) + avg_y * factor

            smoothed.append(StrokePoint(
                x=blend_x,
                y=blend_y,
                pressure=point.pressure,
                velocity=point.velocity,
                time=point.time
            ))

        return smoothed
