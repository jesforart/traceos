from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime
from calibration.models import CalibrationSession, ArtistProfile, CompleteCalibrationRequest
from calibration.profile_generator import ProfileGenerator
from calibration.profile_storage import ProfileStorage

router = APIRouter(prefix="/api/calibration", tags=["calibration"])

profile_generator = ProfileGenerator()
profile_storage = ProfileStorage()

@router.post("/session", response_model=CalibrationSession)
async def start_calibration_session(user_id: Optional[str] = None):
    """Start a new calibration session."""

    session = CalibrationSession(
        id=f"session_{int(datetime.now().timestamp() * 1000)}",
        user_id=user_id,
        strokes=[],
        started_at=int(datetime.now().timestamp() * 1000),
        current_phase="feather"
    )

    return session

@router.post("/session/{session_id}/complete", response_model=ArtistProfile)
async def complete_calibration(
    session_id: str,
    request: CompleteCalibrationRequest
):
    """
    Complete calibration and generate artist profile.

    Analyzes all captured strokes, fits curves, and returns profile.
    """
    try:
        # Generate profile from session
        profile = profile_generator.generate_profile(
            request.session,
            request.artist_name
        )

        # Store profile
        profile_storage.store_profile(profile)

        return profile

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles", response_model=List[ArtistProfile])
async def get_all_profiles():
    """Get all stored artist profiles."""
    return profile_storage.get_all_profiles()

@router.get("/profiles/{profile_id}", response_model=ArtistProfile)
async def get_profile(profile_id: str):
    """Get specific artist profile by ID."""
    profile = profile_storage.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete artist profile."""
    profile_storage.delete_profile(profile_id)
    return {"message": "Profile deleted"}

@router.get("/profiles/{profile_id}/export")
async def export_profile(profile_id: str):
    """Export profile as JSON."""
    json_str = profile_storage.export_to_json(profile_id)
    if not json_str:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"json": json_str}
