import numpy as np
from typing import List, Dict
from .models import (
    CalibrationSession,
    PressureDistribution,
    TiltDistribution,
    VelocityDistribution,
    PhaseDistributions
)

class StrokeAnalyzer:
    """Analyze calibration strokes to extract statistical distributions."""

    def analyze_session(self, session: CalibrationSession) -> Dict[str, PhaseDistributions]:
        """
        Analyze all strokes in a calibration session.

        Returns distributions for each phase (feather, normal, heavy).
        """
        distributions = {}

        for phase in ["feather", "normal", "heavy"]:
            phase_strokes = [s.stroke for s in session.strokes if s.phase == phase]

            if not phase_strokes:
                continue

            distributions[phase] = self.analyze_phase(phase_strokes)

        return distributions

    def analyze_phase(self, strokes: List[dict]) -> PhaseDistributions:
        """Analyze strokes from a single phase."""

        # Extract all point data
        pressures = []
        tilts = []
        azimuths = []
        velocities = []

        for stroke in strokes:
            points = stroke.get("points", [])

            for i, point in enumerate(points):
                pressures.append(point.get("pressure", 0.5))
                tilts.append(point.get("tilt_x", 0))  # Use tilt_x as tilt degree proxy
                azimuths.append(point.get("tilt_y", 0))  # Use tilt_y as azimuth proxy

                # Calculate velocity
                if i > 0:
                    prev = points[i-1]
                    dx = point["x"] - prev["x"]
                    dy = point["y"] - prev["y"]
                    dt = (point["timestamp"] - prev["timestamp"]) / 1000.0  # ms to s

                    if dt > 0:
                        dist = np.sqrt(dx**2 + dy**2)
                        vel = dist / dt  # px/s
                        velocities.append(vel)

        # Compute pressure distribution
        pressure_dist = self._compute_pressure_distribution(pressures)

        # Compute tilt distribution
        tilt_dist = self._compute_tilt_distribution(tilts, azimuths)

        # Compute velocity distribution
        velocity_dist = self._compute_velocity_distribution(velocities)

        return PhaseDistributions(
            pressure=pressure_dist,
            tilt=tilt_dist,
            velocity=velocity_dist
        )

    def _compute_pressure_distribution(self, pressures: List[float]) -> PressureDistribution:
        """Compute pressure statistics."""
        arr = np.array(pressures)

        if len(arr) == 0:
            return PressureDistribution(
                min=0.0,
                max=0.0,
                mean=0.0,
                median=0.0,
                std_dev=0.0,
                histogram=[0]*10
            )

        # Compute histogram (10 bins from 0 to 1)
        hist, _ = np.histogram(arr, bins=10, range=(0, 1))

        return PressureDistribution(
            min=float(np.min(arr)),
            max=float(np.max(arr)),
            mean=float(np.mean(arr)),
            median=float(np.median(arr)),
            std_dev=float(np.std(arr)),
            histogram=hist.tolist()
        )

    def _compute_tilt_distribution(
        self,
        tilts: List[float],
        azimuths: List[float]
    ) -> TiltDistribution:
        """Compute tilt statistics."""
        tilt_arr = np.array(tilts)
        azimuth_arr = np.array(azimuths)

        if len(tilt_arr) == 0:
            return TiltDistribution(
                avg_tilt_deg=0.0,
                avg_azimuth_deg=0.0,
                tilt_range=(0.0, 0.0),
                mode_tilt_deg=0.0
            )

        # Convert to degrees (assuming input is in degrees already)
        # In real implementation, convert from raw sensor values

        return TiltDistribution(
            avg_tilt_deg=float(np.mean(np.abs(tilt_arr))),
            avg_azimuth_deg=float(np.mean(azimuth_arr)),
            tilt_range=(float(np.min(tilt_arr)), float(np.max(tilt_arr))),
            mode_tilt_deg=float(np.median(np.abs(tilt_arr)))
        )

    def _compute_velocity_distribution(self, velocities: List[float]) -> VelocityDistribution:
        """Compute velocity statistics."""
        arr = np.array(velocities)

        if len(arr) == 0:
            return VelocityDistribution(
                avg_velocity=0,
                max_velocity=0,
                p25_velocity=0,
                p75_velocity=0
            )

        return VelocityDistribution(
            avg_velocity=float(np.mean(arr)),
            max_velocity=float(np.max(arr)),
            p25_velocity=float(np.percentile(arr, 25)),
            p75_velocity=float(np.percentile(arr, 75))
        )

    def remove_outliers(self, values: List[float], percentile: float = 95) -> List[float]:
        """
        Remove statistical outliers from data.

        Uses percentile clipping to handle sensor spikes.
        """
        arr = np.array(values)

        if len(arr) == 0:
            return []

        # Compute percentile bounds
        lower = np.percentile(arr, 100 - percentile)
        upper = np.percentile(arr, percentile)

        # Clip to bounds
        clipped = np.clip(arr, lower, upper)

        return clipped.tolist()
