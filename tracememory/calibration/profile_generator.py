import hashlib
import json
from datetime import datetime
from .models import ArtistProfile, CalibrationSession
from .analyzer import StrokeAnalyzer
from .curve_fitter import CurveFitter

# Version constants
TRACE_PROFILE_VERSION = "1.0.0"
BRUSH_ENGINE_VERSION = "2025.11.12"

class ProfileGenerator:
    """Generate complete artist profile from calibration session."""

    def __init__(self):
        self.analyzer = StrokeAnalyzer()
        self.fitter = CurveFitter()

    def generate_profile(
        self,
        session: CalibrationSession,
        artist_name: str = "Artist"
    ) -> ArtistProfile:
        """
        Generate complete artist profile.

        Steps:
        1. Analyze all strokes to get distributions
        2. Generate fingerprint from distributions
        3. Fit curves to distributions
        4. Generate nib parameters
        5. Generate stabilizer settings
        6. Package into ArtistProfile
        """

        # Step 1: Analyze strokes
        distributions = self.analyzer.analyze_session(session)

        # Step 2: Generate fingerprint
        fingerprint = self._generate_fingerprint(distributions)

        # Step 3: Fit curves
        curves = self.fitter.fit_profile_curves(distributions)

        # Step 4: Generate nib parameters
        nib = self._generate_nib_params(distributions)

        # Step 5: Generate stabilizer settings
        stabilizer = self._generate_stabilizer_params(distributions)

        # Step 6: Package profile
        profile = ArtistProfile(
            id=f"profile_{fingerprint}",
            artist_name=artist_name,
            created_at=int(datetime.now().timestamp() * 1000),
            version=1,
            trace_profile_version=TRACE_PROFILE_VERSION,
            brush_engine_version=BRUSH_ENGINE_VERSION,
            device={
                "type": "iPad",
                "stylus": "Apple Pencil",
                "calibration_fingerprint": fingerprint,
                "captured_at": int(datetime.now().timestamp() * 1000)
            },
            distributions={
                phase: {
                    "pressure": dist.pressure.dict(),
                    "tilt": dist.tilt.dict(),
                    "velocity": dist.velocity.dict()
                }
                for phase, dist in distributions.items()
            },
            curves=curves,
            nib=nib,
            stabilizer=stabilizer
        )

        return profile

    def _generate_fingerprint(self, distributions: dict) -> str:
        """
        Generate unique fingerprint for calibration data.

        This creates a reproducible hash of the statistical distributions,
        allowing us to detect identical calibrations across devices.
        """
        # Serialize distributions to stable JSON
        json_str = json.dumps(
            {
                phase: {
                    "pressure": {
                        "mean": dist.pressure.mean,
                        "median": dist.pressure.median,
                        "std_dev": dist.pressure.std_dev
                    },
                    "tilt": {
                        "avg_tilt_deg": dist.tilt.avg_tilt_deg
                    },
                    "velocity": {
                        "avg_velocity": dist.velocity.avg_velocity
                    }
                }
                for phase, dist in distributions.items()
            },
            sort_keys=True
        )

        # Generate SHA1 hash
        hash_obj = hashlib.sha1(json_str.encode())

        # Take first 12 characters (collision chance: ~1 in 16 trillion)
        fingerprint = hash_obj.hexdigest()[:12]

        return fingerprint

    def _generate_nib_params(self, distributions: dict) -> dict:
        """Generate nib parameters from distributions."""

        normal = distributions.get("normal")
        if not normal:
            # Fallback defaults
            return {
                "baseRadiusPx": 2.0,
                "minRadiusPx": 0.4,
                "maxRadiusPx": 12.0,
                "avgTiltDeg": 35.0
            }

        # Base radius from normal pressure mean
        # Higher pressure users get slightly larger base
        pressure_factor = normal.pressure.mean
        base_radius = 1.5 + (pressure_factor * 1.5)  # 1.5-3.0 range

        return {
            "baseRadiusPx": round(base_radius, 2),
            "minRadiusPx": 0.4,
            "maxRadiusPx": round(base_radius * 6, 1),
            "avgTiltDeg": round(normal.tilt.avg_tilt_deg, 1)
        }

    def _generate_stabilizer_params(self, distributions: dict) -> dict:
        """Generate stabilizer parameters from distributions."""

        normal = distributions.get("normal")
        if not normal:
            # Fallback defaults
            return {
                "microJitterRadiusPx": 2.0,
                "curveSmooth": {"min": 0.05, "max": 0.20},
                "velocityAdapt": {"vMin": 0.0, "vMax": 1500.0}
            }

        # Jitter radius based on velocity variance
        # High velocity users need more stabilization
        v_range = normal.velocity.p75_velocity - normal.velocity.p25_velocity
        jitter_radius = 1.5 + (v_range / 1000.0)  # Scale by velocity range

        # Smoothing range
        # Adapt to user's natural speed
        v_max = max(normal.velocity.max_velocity, 1000.0)

        return {
            "microJitterRadiusPx": round(min(jitter_radius, 3.5), 2),
            "curveSmooth": {
                "min": 0.03,
                "max": 0.25
            },
            "velocityAdapt": {
                "vMin": 0.0,
                "vMax": round(v_max * 1.2, 1)
            }
        }
