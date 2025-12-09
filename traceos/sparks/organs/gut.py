"""
Gut Spark - Affective Organ

Focus: UX, vibe, naming, emotional resonance.
Now with Quantum Stabilization for resolving internal tension.

@provenance traceos_sparks_v1
@organ affective
"""

import logging
from datetime import datetime
from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata
from traceos.protocol.schemas import DeriveOutput, SparkReview, SparkComment

logger = logging.getLogger(__name__)


class GutSpark(SparkBase):
    """
    Gut Spark evaluates emotional resonance and UX quality.

    Heuristics:
    - Intent tag analysis (quantum = excitement)
    - Keyword detection (stub, hack, todo = unease)
    - Naming quality
    """

    def _define_metadata(self) -> SparkMetadata:
        return SparkMetadata(
            name="Gut",
            organ_type="affective",
            description="Intuition, taste, and emotional resonance",
            version="1.0"
        )

    def evaluate(self, derivation: DeriveOutput) -> SparkReview:
        """Evaluate emotional and UX quality."""
        score = 0.7  # Baseline positive
        comments = []
        mood = "neutral"

        # Check derivation notes for concerning keywords
        notes_lower = derivation.notes.lower()

        concerning_keywords = ["stub", "hack", "todo", "fixme", "broken"]
        found_concerns = [kw for kw in concerning_keywords if kw in notes_lower]

        if found_concerns:
            comments.append(SparkComment(
                severity="medium",
                message=f"Detected technical debt markers: {', '.join(found_concerns)}"
            ))
            score -= 0.1 * len(found_concerns)
            mood = "uneasy"

        # Check for positive signals
        positive_keywords = ["quantum", "energy", "landscape", "dna", "spark"]
        found_positive = [kw for kw in positive_keywords if kw in notes_lower]

        if found_positive:
            comments.append(SparkComment(
                severity="info",
                message=f"Resonates with TraceOS vision: {', '.join(found_positive)}"
            ))
            score += 0.1
            mood = "excited"

        # Update Gut state
        self.update_state(
            activation=0.9,  # Gut is highly active
            mood=mood
        )

        # Determine status
        if score >= 0.8:
            status = "approve"
        elif score >= 0.6:
            status = "approve-with-changes"
        else:
            status = "reject"

        return SparkReview(
            spark="Gut",
            status=status,
            score=min(1.0, max(0.0, score)),
            comments=comments
        )

    async def stabilize(self) -> dict:
        """
        Attempt to resolve internal tension using Quantum Annealing.

        Constructs an energy landscape representing internal conflict,
        submits it to the Quantum Organ for minimization, and updates
        Gut state based on the result.
        """
        # Import here to avoid circular imports
        from traceos.quantum.landscape import EnergyLandscape
        from traceos.quantum.classical_backend import ClassicalSimCoprocessor
        from traceos.quantum.jobs import QuantumJobStore

        # Skip if already in flow
        if self.state.mood == "flow":
            return {"status": "skipped", "reason": "already_in_flow"}

        logger.info("Gut attempting quantum stabilization...")

        # 1. Construct the Energy Landscape of current tension
        # Biases: baseline preferences for speed, quality, novelty
        # Tensions: conflicts between these dimensions
        landscape = EnergyLandscape(
            dimensions=["speed", "quality", "novelty"],
            biases={
                "speed": 0.5,     # Slight preference for speed
                "quality": 0.5,   # Slight preference for quality
                "novelty": 0.2    # Smaller preference for novelty
            },
            tensions={
                "speed|quality": 1.0,    # Strong conflict between speed and quality
                "speed|novelty": -0.5,   # Speed and novelty synergize
                "quality|novelty": 0.5   # Quality and novelty have mild tension
            }
        )

        # 2. Submit to Quantum Organ
        job_id = f"gut_stabilize_{int(datetime.utcnow().timestamp())}"
        coprocessor = ClassicalSimCoprocessor()
        result = await coprocessor.submit_job(landscape.to_job(job_id, "Gut"))

        # 3. Persist Result
        QuantumJobStore().save(result)

        # 4. React to the Solution
        # If energy is low enough, we found a "Flow State"
        if result.energy < -0.5:
            self.update_state(
                mood="flow",
                memory={
                    "last_quantum_fix": result.job_id,
                    "solution": result.solution,
                    "energy_achieved": result.energy
                }
            )
            logger.info(f"Gut stabilized! Energy: {result.energy:.3f}, Mood → flow")
            return {
                "status": "stabilized",
                "energy": result.energy,
                "solution": result.solution,
                "execution_time_ms": result.execution_time_ms
            }

        logger.warning(f"Gut stabilization failed. Energy: {result.energy:.3f}")
        return {
            "status": "failed_to_stabilize",
            "energy": result.energy,
            "reason": "energy_threshold_not_reached"
        }
