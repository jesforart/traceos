"""
Dual DNA Engine - Logic shell for Cognitive Kernel v2.5

RED TEAM FIX #4: All vector computation validates 128-dim output.

This is a PLACEHOLDER implementation (v1). Vector computation uses simple
statistical heuristics, NOT production-grade ML inference.

Architecture: Proper delegation pattern - no god-object.
Dependencies injected: MemoryStorage, TelemetryStore
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from tracememory.models.memory import (
    CognitiveMemoryBlock, StyleDNA, IntentProfile, TelemetryChunk,
    STYLE_VECTOR_DIM, validate_vector_dim
)
from tracememory.storage.memory_storage import MemoryStorage
from tracememory.storage.telemetry_store import TelemetryStore


class DualDNAEngine:
    """
    Dual DNA Engine - Ingestion pipeline for Cognitive Kernel v2.5

    Responsibilities:
    1. Ingest artifacts (SVG, PNG, stroke data) into tri-state memory
    2. Compute placeholder style vectors (128-dim, validated)
    3. Link Logic/Vibe/Mind layers via composite keys

    RED TEAM FIX #4: All vectors validated to be exactly 128-dim.
    """

    def __init__(
        self,
        memory_storage: MemoryStorage,
        telemetry_store: Optional[TelemetryStore] = None
    ):
        """
        Initialize DualDNAEngine with injected dependencies.

        Args:
            memory_storage: MemoryStorage instance for tri-state persistence
            telemetry_store: Optional TelemetryStore for stroke telemetry
        """
        self.storage = memory_storage
        self.telemetry = telemetry_store

    def ingest_artifact(
        self,
        session_id: str,
        artifact_id: str,
        svg_data: Optional[str] = None,
        image_data: Optional[np.ndarray] = None,
        strokes: Optional[List[Dict]] = None,
        intent: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Tuple[str, str, Optional[str]]:
        """
        Ingest artifact into tri-state memory with validated vectors.

        Pipeline:
        1. Save stroke telemetry (if provided) → TelemetryChunk
        2. Compute placeholder StyleDNA vectors (128-dim, validated)
        3. Create IntentProfile (if intent provided)
        4. Create CognitiveMemoryBlock linking all layers

        Args:
            session_id: Session identifier
            artifact_id: Artifact identifier (unique per session)
            svg_data: Optional SVG string
            image_data: Optional rasterized image (H, W, C) numpy array
            strokes: Optional stroke telemetry list
            intent: Optional intent dict {emotional_register, target_audience, ...}
            tags: Optional tags for memory block
            notes: Optional notes

        Returns:
            Tuple of (memory_block_id, style_dna_id, intent_profile_id)

        RED TEAM FIX #3: Uses composite key (session_id, artifact_id)
        RED TEAM FIX #4: Validates all vectors are 128-dim
        """
        # Step 1: Save stroke telemetry (optional)
        telemetry_chunk = None
        if strokes and self.telemetry:
            telemetry_chunk = self.telemetry.save_strokes(
                session_id=session_id,
                artifact_id=artifact_id,
                strokes=strokes
            )
            # Persist chunk metadata to MemoryStorage
            self.storage.save_telemetry_chunk(telemetry_chunk)

        # Step 2: Compute StyleDNA with validated 128-dim vectors
        stroke_dna = self._compute_stroke_dna(strokes) if strokes else None
        image_dna = self._compute_image_dna(image_data) if image_data is not None else None
        temporal_dna = self._compute_temporal_dna(strokes) if strokes else None

        # HARDENING v2.6 - Task 4: Auto-generate checksum and L2 norm
        from tracememory.storage.vector_utils import compute_style_dna_checksum, compute_l2_norm

        checksum = compute_style_dna_checksum(stroke_dna, image_dna, temporal_dna)
        l2_norm = compute_l2_norm(stroke_dna) if stroke_dna else None

        style = StyleDNA(
            artifact_id=artifact_id,
            stroke_dna=stroke_dna,
            image_dna=image_dna,
            temporal_dna=temporal_dna,
            l2_norm=l2_norm,
            checksum=checksum
        )
        # Pydantic validators ensure 128-dim on construction
        style_dna_id = self.storage.save_style_dna(style)

        # Step 3: Create IntentProfile (optional)
        intent_profile_id = None
        if intent:
            intent_obj = IntentProfile(
                session_id=session_id,
                artifact_id=artifact_id,
                emotional_register=intent.get("emotional_register", {}),
                target_audience=intent.get("target_audience"),
                constraints=intent.get("constraints", []),
                narrative_prompt=intent.get("narrative_prompt"),
                style_keywords=intent.get("style_keywords", []),
                source=intent.get("source", "user_prompt")
            )
            intent_profile_id = self.storage.save_intent_profile(intent_obj)

        # Step 4: Create CognitiveMemoryBlock linking all layers
        memory_block = CognitiveMemoryBlock(
            session_id=session_id,
            artifact_id=artifact_id,
            intent_profile_id=intent_profile_id,
            style_dna_id=style_dna_id,
            tags=tags or [],
            notes=notes
        )
        # RED TEAM FIX #3: Composite uniqueness enforced in storage layer
        memory_block_id = self.storage.save_cognitive_memory_block(memory_block)

        return (memory_block_id, style_dna_id, intent_profile_id)

    def get_dual_profile(
        self,
        session_id: str,
        artifact_id: str
    ) -> Optional[Dict]:
        """
        Retrieve full dual profile using composite key.

        RED TEAM FIX #3: Uses composite key (session_id, artifact_id) for retrieval.

        Args:
            session_id: Session identifier
            artifact_id: Artifact identifier

        Returns:
            Dict with {memory_block, style_dna, intent_profile} or None
        """
        # Retrieve via composite key
        memory_block = self.storage.get_cognitive_memory_block_by_artifact(
            session_id=session_id,
            artifact_id=artifact_id
        )

        if not memory_block:
            return None

        # Fetch linked records
        style_dna = None
        if memory_block.style_dna_id:
            style_dna = self.storage.get_style_dna(memory_block.style_dna_id)

        intent_profile = None
        if memory_block.intent_profile_id:
            intent_profile = self.storage.get_intent_profile(memory_block.intent_profile_id)

        return {
            "memory_block": memory_block,
            "style_dna": style_dna,
            "intent_profile": intent_profile
        }

    # ==============================================================================
    # PLACEHOLDER VECTOR COMPUTATION (v1 - NOT PRODUCTION ML)
    # ==============================================================================

    def _compute_stroke_dna(self, strokes: List[Dict]) -> List[float]:
        """
        Compute 128-dim stroke DNA from telemetry using statistical heuristics.

        PLACEHOLDER v1: Simple statistical features, NOT production ML inference.

        RED TEAM FIX #4: Output validated to be exactly 128-dim.

        Args:
            strokes: List of stroke dicts with keys: x, y, p, t, tilt

        Returns:
            128-dim vector (validated)
        """
        if not strokes:
            # Zero vector for empty input
            return validate_vector_dim([0.0] * STYLE_VECTOR_DIM, STYLE_VECTOR_DIM)

        # Extract arrays
        x = np.array([s.get('x', 0.0) for s in strokes])
        y = np.array([s.get('y', 0.0) for s in strokes])
        p = np.array([s.get('p', 0.5) for s in strokes])
        t = np.array([s.get('t', 0.0) for s in strokes])
        tilt = np.array([s.get('tilt', 0.0) for s in strokes])

        # Compute statistical features (simple heuristics)
        features = []

        # Spatial statistics (32 dims)
        features.extend([
            float(np.mean(x)), float(np.std(x)), float(np.min(x)), float(np.max(x)),
            float(np.mean(y)), float(np.std(y)), float(np.min(y)), float(np.max(y)),
            float(np.mean(p)), float(np.std(p)), float(np.min(p)), float(np.max(p)),
            float(np.mean(tilt)), float(np.std(tilt)), float(np.min(tilt)), float(np.max(tilt)),
        ])

        # Velocity features (16 dims)
        if len(x) > 1:
            dx = np.diff(x)
            dy = np.diff(y)
            velocity = np.sqrt(dx**2 + dy**2)
            features.extend([
                float(np.mean(velocity)), float(np.std(velocity)),
                float(np.min(velocity)), float(np.max(velocity)),
                float(np.median(velocity)), float(np.percentile(velocity, 25)),
                float(np.percentile(velocity, 75)), float(np.percentile(velocity, 90)),
            ])
        else:
            features.extend([0.0] * 8)

        # Pressure dynamics (8 dims)
        if len(p) > 1:
            dp = np.diff(p)
            features.extend([
                float(np.mean(dp)), float(np.std(dp)),
                float(np.min(dp)), float(np.max(dp)),
            ])
        else:
            features.extend([0.0] * 4)

        # Temporal features (8 dims)
        if len(t) > 1:
            dt = np.diff(t)
            features.extend([
                float(np.mean(dt)), float(np.std(dt)),
                float(np.min(dt)), float(np.max(dt)),
            ])
        else:
            features.extend([0.0] * 4)

        # Pad remaining dimensions to reach 128
        current_len = len(features)
        if current_len < STYLE_VECTOR_DIM:
            features.extend([0.0] * (STYLE_VECTOR_DIM - current_len))

        # Ensure exactly 128 dims
        features = features[:STYLE_VECTOR_DIM]

        # Validate before return (RED TEAM FIX #4)
        return validate_vector_dim(features, STYLE_VECTOR_DIM)

    def _compute_image_dna(self, image: np.ndarray) -> List[float]:
        """
        Compute 128-dim image DNA from raster using statistical heuristics.

        PLACEHOLDER v1: Simple pixel statistics, NOT production ML inference.

        RED TEAM FIX #4: Output validated to be exactly 128-dim.

        Args:
            image: Numpy array (H, W, C) or (H, W)

        Returns:
            128-dim vector (validated)
        """
        if image is None or image.size == 0:
            return validate_vector_dim([0.0] * STYLE_VECTOR_DIM, STYLE_VECTOR_DIM)

        # Flatten image
        flat = image.flatten()

        features = []

        # Global statistics (16 dims)
        features.extend([
            float(np.mean(flat)), float(np.std(flat)),
            float(np.min(flat)), float(np.max(flat)),
            float(np.median(flat)), float(np.percentile(flat, 25)),
            float(np.percentile(flat, 75)), float(np.percentile(flat, 90)),
        ])

        # Histogram features (16 bins = 16 dims)
        hist, _ = np.histogram(flat, bins=16, range=(0, 255))
        hist_norm = hist / (np.sum(hist) + 1e-8)  # Normalize
        features.extend([float(h) for h in hist_norm])

        # Edge density heuristic (8 dims)
        if len(image.shape) >= 2:
            # Simple gradient magnitude
            gy, gx = np.gradient(image[:, :, 0] if len(image.shape) == 3 else image)
            grad_mag = np.sqrt(gx**2 + gy**2)
            features.extend([
                float(np.mean(grad_mag)), float(np.std(grad_mag)),
                float(np.min(grad_mag)), float(np.max(grad_mag)),
            ])
        else:
            features.extend([0.0] * 4)

        # Pad remaining dimensions to reach 128
        current_len = len(features)
        if current_len < STYLE_VECTOR_DIM:
            features.extend([0.0] * (STYLE_VECTOR_DIM - current_len))

        # Ensure exactly 128 dims
        features = features[:STYLE_VECTOR_DIM]

        # Validate before return (RED TEAM FIX #4)
        return validate_vector_dim(features, STYLE_VECTOR_DIM)

    def _compute_temporal_dna(self, strokes: List[Dict]) -> List[float]:
        """
        Compute 128-dim temporal DNA from stroke timing using statistical heuristics.

        PLACEHOLDER v1: Simple rhythm features, NOT production ML inference.

        RED TEAM FIX #4: Output validated to be exactly 128-dim.

        Args:
            strokes: List of stroke dicts with keys: x, y, p, t, tilt

        Returns:
            128-dim vector (validated)
        """
        if not strokes or len(strokes) < 2:
            return validate_vector_dim([0.0] * STYLE_VECTOR_DIM, STYLE_VECTOR_DIM)

        # Extract timestamps
        t = np.array([s.get('t', 0.0) for s in strokes])

        features = []

        # Timestamp statistics (8 dims)
        features.extend([
            float(np.mean(t)), float(np.std(t)),
            float(np.min(t)), float(np.max(t)),
        ])

        # Inter-stroke intervals (16 dims)
        dt = np.diff(t)
        if len(dt) > 0:
            features.extend([
                float(np.mean(dt)), float(np.std(dt)),
                float(np.min(dt)), float(np.max(dt)),
                float(np.median(dt)), float(np.percentile(dt, 25)),
                float(np.percentile(dt, 75)), float(np.percentile(dt, 90)),
            ])
        else:
            features.extend([0.0] * 8)

        # Rhythm histogram (16 bins = 16 dims)
        if len(dt) > 0:
            hist, _ = np.histogram(dt, bins=16)
            hist_norm = hist / (np.sum(hist) + 1e-8)
            features.extend([float(h) for h in hist_norm])
        else:
            features.extend([0.0] * 16)

        # Acceleration features (8 dims)
        if len(dt) > 1:
            ddt = np.diff(dt)
            features.extend([
                float(np.mean(ddt)), float(np.std(ddt)),
                float(np.min(ddt)), float(np.max(ddt)),
            ])
        else:
            features.extend([0.0] * 4)

        # Pad remaining dimensions to reach 128
        current_len = len(features)
        if current_len < STYLE_VECTOR_DIM:
            features.extend([0.0] * (STYLE_VECTOR_DIM - current_len))

        # Ensure exactly 128 dims
        features = features[:STYLE_VECTOR_DIM]

        # Validate before return (RED TEAM FIX #4)
        return validate_vector_dim(features, STYLE_VECTOR_DIM)
