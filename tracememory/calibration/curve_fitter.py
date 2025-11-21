import numpy as np
from typing import List, Tuple, Dict
from .models import BezierCurve, PhaseDistributions

class CurveFitter:
    """Fit Bezier curves to calibration data."""

    def fit_profile_curves(
        self,
        distributions: Dict[str, PhaseDistributions]
    ) -> dict:
        """
        Fit all curves needed for artist profile.

        Returns dict with:
        - pressureToRadius: Bezier curve
        - pressureToDensity: Bezier curve
        - velocityToOpacity: Points array
        - velocityToSoftness: Points array
        """

        # Extract key distributions
        feather = distributions.get("feather")
        normal = distributions.get("normal")
        heavy = distributions.get("heavy")

        if not all([feather, normal, heavy]):
            raise ValueError("Missing phase data")

        # Fit pressure curves
        pressure_to_radius = self._fit_pressure_to_radius(feather, normal, heavy)
        pressure_to_density = self._fit_pressure_to_density(feather, normal, heavy)

        # Fit velocity curves
        velocity_to_opacity = self._fit_velocity_to_opacity(normal)
        velocity_to_softness = self._fit_velocity_to_softness(normal)

        return {
            "pressureToRadius": {
                "controlPoints": pressure_to_radius.control_points
            },
            "pressureToDensity": {
                "controlPoints": pressure_to_density.control_points
            },
            "velocityToOpacity": velocity_to_opacity,
            "velocityToSoftness": velocity_to_softness
        }

    def _fit_pressure_to_radius(
        self,
        feather: PhaseDistributions,
        normal: PhaseDistributions,
        heavy: PhaseDistributions
    ) -> BezierCurve:
        """
        Fit pressure → radius curve.

        Strategy:
        - Feather phase defines low-pressure response
        - Normal phase defines mid-range
        - Heavy phase defines high-pressure response
        """

        # Define key points based on phase means
        p_feather = feather.pressure.mean
        p_normal = normal.pressure.mean
        p_heavy = heavy.pressure.mean

        # Target radius values (normalized 0-1)
        # Feather should be visible (0.15), normal medium (0.5), heavy full (1.0)

        # Construct Bezier control points
        # P0 = (0, 0) - zero pressure, zero radius
        # P1 = (p_feather * 1.5, 0.15) - feather influence
        # P2 = (p_normal, 0.7) - normal range
        # P3 = (1.0, 1.0) - full pressure

        control_points = [
            (0.0, 0.0),
            (min(p_feather * 2.0, 0.3), 0.15),
            (min(p_normal * 1.2, 0.7), 0.7),
            (1.0, 1.0)
        ]

        return BezierCurve(control_points=control_points)

    def _fit_pressure_to_density(
        self,
        feather: PhaseDistributions,
        normal: PhaseDistributions,
        heavy: PhaseDistributions
    ) -> BezierCurve:
        """
        Fit pressure → density (opacity) curve.

        Similar to radius but with different response.
        """

        p_feather = feather.pressure.mean
        p_normal = normal.pressure.mean
        p_heavy = heavy.pressure.mean

        # Density ramps up more aggressively than radius
        control_points = [
            (0.0, 0.0),
            (min(p_feather * 1.8, 0.25), 0.25),
            (min(p_normal * 1.1, 0.6), 0.85),
            (1.0, 1.0)
        ]

        return BezierCurve(control_points=control_points)

    def _fit_velocity_to_opacity(self, normal: PhaseDistributions) -> List[Tuple[float, float]]:
        """
        Fit velocity → opacity curve.

        Fast strokes should be slightly less opaque (feathered).
        """

        v_avg = normal.velocity.avg_velocity
        v_max = normal.velocity.max_velocity

        # Define points based on observed velocities
        return [
            (0.0, 1.0),
            (v_avg * 0.5, 0.95),
            (v_avg, 0.85),
            (v_avg * 1.5, 0.75),
            (min(v_max, v_avg * 2.5), 0.65)
        ]

    def _fit_velocity_to_softness(self, normal: PhaseDistributions) -> List[Tuple[float, float]]:
        """
        Fit velocity → edge softness curve.

        Fast strokes should have softer edges.
        """

        v_avg = normal.velocity.avg_velocity
        v_max = normal.velocity.max_velocity

        return [
            (0.0, 1.0),
            (v_avg * 0.7, 0.92),
            (v_avg * 1.2, 0.80),
            (min(v_max, v_avg * 2.0), 0.72)
        ]

    def evaluate_bezier(self, curve: BezierCurve, t: float) -> Tuple[float, float]:
        """
        Evaluate cubic Bezier at parameter t (0-1).

        Uses De Casteljau's algorithm.
        """
        p0, p1, p2, p3 = curve.control_points

        # Linear interpolations
        q0 = self._lerp_point(p0, p1, t)
        q1 = self._lerp_point(p1, p2, t)
        q2 = self._lerp_point(p2, p3, t)

        r0 = self._lerp_point(q0, q1, t)
        r1 = self._lerp_point(q1, q2, t)

        return self._lerp_point(r0, r1, t)

    def _lerp_point(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        t: float
    ) -> Tuple[float, float]:
        """Linear interpolation between two points."""
        return (
            p1[0] + (p2[0] - p1[0]) * t,
            p1[1] + (p2[1] - p1[1]) * t
        )
