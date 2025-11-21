"""
Replay API endpoints

Week 3 - Option D: Next-Gen Replay Engine
FastAPI routes for provenance and temporal features
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import json
import os
from datetime import datetime

from .models import (
    ProvenanceRecord,
    AuthenticityResult,
    AuthenticityComponents,
    TemporalFeatures,
    TemporalProfileUpdate
)

router = APIRouter(prefix="/replay", tags=["replay"])

# In-memory storage (replace with database in production)
provenance_records: List[ProvenanceRecord] = []


@router.post("/provenance/records", response_model=ProvenanceRecord)
async def create_provenance_record(record: ProvenanceRecord):
    """
    Create a new provenance record with temporal features
    """
    # Check if record already exists
    existing = next((r for r in provenance_records if r.id == record.id), None)
    if existing:
        raise HTTPException(status_code=409, detail="Record already exists")

    provenance_records.append(record)

    print(f"[Replay] Created provenance record: {record.id}")
    print(f"[Replay] Session: {record.session_id}, Artist: {record.artist_profile_id}")
    print(f"[Replay] Total strokes: {record.temporal.total_strokes}")
    print(f"[Replay] Momentum mean: {record.temporal.momentum['overall'].mean:.2f}")

    return record


@router.get("/provenance/records", response_model=List[ProvenanceRecord])
async def query_provenance_records(
    artist_profile_id: Optional[str] = Query(None, alias="artistProfileId"),
    start_time: Optional[int] = Query(None, alias="startTime"),
    end_time: Optional[int] = Query(None, alias="endTime"),
    min_duration: Optional[float] = Query(None, alias="minDuration"),
    max_duration: Optional[float] = Query(None, alias="maxDuration"),
    min_strokes: Optional[int] = Query(None, alias="minStrokes")
):
    """
    Query provenance records by temporal criteria
    """
    filtered_records = provenance_records

    # Filter by artist profile ID
    if artist_profile_id:
        filtered_records = [r for r in filtered_records if r.artist_profile_id == artist_profile_id]

    # Filter by timestamp range
    if start_time:
        filtered_records = [r for r in filtered_records if r.timestamp >= start_time]

    if end_time:
        filtered_records = [r for r in filtered_records if r.timestamp <= end_time]

    # Filter by session duration
    if min_duration is not None:
        filtered_records = [r for r in filtered_records if r.temporal.session_duration >= min_duration]

    if max_duration is not None:
        filtered_records = [r for r in filtered_records if r.temporal.session_duration <= max_duration]

    # Filter by stroke count
    if min_strokes is not None:
        filtered_records = [r for r in filtered_records if r.temporal.total_strokes >= min_strokes]

    print(f"[Replay] Query returned {len(filtered_records)} records")

    return filtered_records


@router.get("/provenance/records/{record_id}", response_model=ProvenanceRecord)
async def get_provenance_record(record_id: str):
    """
    Get a specific provenance record by ID
    """
    record = next((r for r in provenance_records if r.id == record_id), None)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return record


@router.patch("/provenance/records/{record_id}/authenticity")
async def update_authenticity_score(record_id: str, body: dict):
    """
    Update the authenticity score for a provenance record
    """
    record = next((r for r in provenance_records if r.id == record_id), None)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    authenticity_score = body.get("authenticityScore")
    if authenticity_score is None:
        raise HTTPException(status_code=400, detail="authenticityScore required")

    record.authenticity_score = authenticity_score

    print(f"[Replay] Updated authenticity score for {record_id}: {authenticity_score:.2f}")

    return {"status": "ok", "authenticityScore": authenticity_score}


@router.post("/provenance/verify", response_model=AuthenticityResult)
async def verify_authenticity(body: dict):
    """
    Verify authenticity of temporal features against artist baseline

    This is a simplified implementation. In production, this would:
    - Load artist baseline from database
    - Compare temporal features using statistical models
    - Apply machine learning models for anomaly detection
    """
    temporal_features = body.get("temporal")
    artist_profile_id = body.get("artistProfileId")

    if not temporal_features or not artist_profile_id:
        raise HTTPException(status_code=400, detail="temporal and artistProfileId required")

    # Get artist's historical records
    artist_records = [r for r in provenance_records if r.artist_profile_id == artist_profile_id]

    if len(artist_records) == 0:
        # No baseline - return moderate confidence
        return AuthenticityResult(
            score=0.75,
            confidence=0.5,
            components=AuthenticityComponents(
                temporal_consistency=0.75,
                device_fingerprint=0.75,
                style_consistency=0.75,
                pause_pattern=0.75
            ),
            flags=["no_baseline"]
        )

    # Calculate baseline from historical records
    momentum_values = [r.temporal.momentum["overall"].mean for r in artist_records]
    velocity_values = [r.temporal.velocity.mean_smoothed for r in artist_records]

    baseline_momentum = sum(momentum_values) / len(momentum_values)
    baseline_velocity = sum(velocity_values) / len(velocity_values)

    # Compare with current session
    current_momentum = temporal_features["momentum"]["overall"]["mean"]
    current_velocity = temporal_features["velocity"]["meanSmoothed"]

    momentum_diff = abs(current_momentum - baseline_momentum) / baseline_momentum if baseline_momentum > 0 else 0
    velocity_diff = abs(current_velocity - baseline_velocity) / baseline_velocity if baseline_velocity > 0 else 0

    # Simple scoring (in production, use ML models)
    temporal_consistency = max(0, 1 - momentum_diff) * 0.5 + max(0, 1 - velocity_diff) * 0.5

    # Device fingerprint (simplified)
    device_fingerprint = 0.9  # Assume consistent device for now

    # Style consistency (based on stroke class distribution)
    style_consistency = 0.85  # Simplified

    # Pause pattern (based on rhythm metrics)
    pause_pattern = 0.8  # Simplified

    # Overall score (weighted average)
    score = (
        temporal_consistency * 0.4 +
        device_fingerprint * 0.2 +
        style_consistency * 0.2 +
        pause_pattern * 0.2
    )

    # Flags
    flags = []
    if score < 0.5:
        flags.append("low_authenticity")
    if temporal_consistency < 0.6:
        flags.append("temporal_anomaly")

    # Confidence based on baseline sample size
    confidence = min(1.0, len(artist_records) / 10)

    print(f"[Replay] Authenticity verification for {artist_profile_id}")
    print(f"[Replay] Score: {score:.2f}, Confidence: {confidence:.2f}")

    return AuthenticityResult(
        score=score,
        confidence=confidence,
        components=AuthenticityComponents(
            temporal_consistency=temporal_consistency,
            device_fingerprint=device_fingerprint,
            style_consistency=style_consistency,
            pause_pattern=pause_pattern
        ),
        flags=flags
    )


@router.get("/provenance/baseline/{artist_profile_id}", response_model=TemporalFeatures)
async def get_artist_baseline(artist_profile_id: str):
    """
    Get temporal baseline for an artist (aggregate statistics)
    """
    artist_records = [r for r in provenance_records if r.artist_profile_id == artist_profile_id]

    if len(artist_records) == 0:
        raise HTTPException(status_code=404, detail="No records found for artist")

    # Aggregate statistics
    total_strokes = sum(r.temporal.total_strokes for r in artist_records)
    total_duration = sum(r.temporal.session_duration for r in artist_records)

    momentum_values = [r.temporal.momentum["overall"].mean for r in artist_records]
    velocity_values = [r.temporal.velocity.mean_smoothed for r in artist_records]

    # Create baseline temporal features (simplified)
    baseline = artist_records[0].temporal.copy()
    baseline.session_id = "baseline"
    baseline.total_strokes = total_strokes
    baseline.session_duration = total_duration

    # Update with aggregate values
    baseline.momentum["overall"].mean = sum(momentum_values) / len(momentum_values)
    baseline.velocity.mean_smoothed = sum(velocity_values) / len(velocity_values)

    print(f"[Replay] Retrieved baseline for {artist_profile_id} ({len(artist_records)} sessions)")

    return baseline


@router.patch("/calibration/profiles/{profile_id}/temporal")
async def update_profile_temporal(profile_id: str, update: TemporalProfileUpdate):
    """
    Update artist profile with temporal features

    In production, this would update the calibration profile in the database
    """
    print(f"[Replay] Updating temporal features for profile: {profile_id}")
    print(f"[Replay] Momentum mean: {update.momentum_mean:.2f}")
    print(f"[Replay] Velocity mean: {update.velocity_mean:.2f}")
    print(f"[Replay] Sessions: {update.session_count}")

    # In production, update database here
    # For now, just acknowledge the update

    return {
        "status": "ok",
        "profileId": profile_id,
        "temporalUpdated": True
    }


@router.get("/health")
async def replay_health_check():
    """
    Health check endpoint for replay system
    """
    return {
        "status": "ok",
        "service": "replay",
        "records_count": len(provenance_records)
    }
