"""
Eyes Spark - Vision Organ v2

Now oriented around visual perception of rendered artifacts.
For Phase 6, we:
- Detect visual work via derivation context
- Stub an internal 'analyze_visual_density' pipeline
- Calibrate against DNA for style continuity

Future phases will:
- Load actual PNGs
- Perform histogram / edge / density analysis

@provenance traceos_sparks_v2
@organ visual
"""

import logging

from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata
from traceos.protocol.schemas import DeriveOutput, SparkReview, SparkComment
from traceos.dna.store import DNAStore

logger = logging.getLogger(__name__)


class EyesSpark(SparkBase):
    """
    Eyes Spark (Vision Organ v2).

    Capabilities:
    - Detects presence of visual artifacts in derivation notes
    - Conceptually 'looks at' visuals (stubbed)
    - Aligns perceptions with current creative DNA
    """

    def _define_metadata(self) -> SparkMetadata:
        return SparkMetadata(
            name="Eyes",
            organ_type="visual",
            description="Visual perception and stroke quality analysis",
            version="2.0"
        )

    def evaluate(self, derivation: DeriveOutput) -> SparkReview:
        """
        Visual evaluation pipeline.

        Phase 6: Conceptual vision (detects visual markers in notes)
        Phase 7+: Actual pixel analysis
        """
        score = 0.8
        comments = []

        notes_lower = derivation.notes.lower()

        # 1. Detect visual work heuristically
        visual_markers = ["stroke", "canvas", "render", "image", "png"]
        if any(marker in notes_lower for marker in visual_markers):
            comments.append(SparkComment(
                severity="info",
                message="Visual content indicators detected in derivation notes"
            ))
            # Stub call into visual analysis pipeline
            self._analyze_visual_density()
            score += 0.05

        # 2. Check for documentation (v1 behavior preserved)
        doc_files = [
            f for f in derivation.files
            if any(ext in f.path.lower() for ext in ['.md', 'readme', 'doc'])
        ]

        if doc_files:
            comments.append(SparkComment(
                severity="info",
                message=f"Found {len(doc_files)} documentation files"
            ))
            score += 0.05

        # 3. Check for visual assets (v1 behavior preserved)
        visual_files = [
            f for f in derivation.files
            if any(ext in f.path.lower() for ext in ['.svg', '.png', 'diagram'])
        ]

        if visual_files:
            comments.append(SparkComment(
                severity="info",
                message=f"Contains {len(visual_files)} visual assets"
            ))
            score += 0.05

        # 4. Calibrate against latest DNA signature
        dna_store = DNAStore()
        latest = dna_store.get_latest_signature()
        if latest:
            comments.append(SparkComment(
                severity="info",
                message=f"Calibrating visual judgment against DNA: {latest.signature_id[:30]}..."
            ))
            # Future: use DNA metrics to bias scoring

        # Update state: Eyes worked, so fatigue slightly increases
        self.update_state(
            activation=0.9,
            fatigue=min(1.0, self.state.fatigue + 0.05)
        )

        status = "approve"

        return SparkReview(
            spark="Eyes",
            status=status,
            score=min(1.0, score),
            comments=comments
        )

    def _analyze_visual_density(self) -> None:
        """
        Stub for future computer vision.

        Phase 7+ will:
        - Load PNG from ./data/artifacts/visuals
        - Compute pixel density, contrast, edge maps, etc.
        - Feed results back into Eyes state/DNA.

        For now, this merely logs the action.
        """
        logger.debug("EyesSpark: Stub visual density analysis invoked")
