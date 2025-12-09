"""
Energy Landscape for TraceOS Quantum Organ

Represents emotional or constraint landscapes that can be
minimized through quantum-style annealing.

@provenance traceos_quantum_v1
@organ quantum
"""

from typing import List, Dict
from pydantic import BaseModel
from .schemas import QuantumJobSpec, QuantumProblemType


class EnergyLandscape(BaseModel):
    """
    Represents the emotional or constraints landscape of an organ.
    Converts high-level 'tensions' into a Hamiltonian for the solver.
    """
    dimensions: List[str]
    tensions: Dict[str, float]  # 'speed|accuracy': 1.0 (conflict)
    biases: Dict[str, float] = {}

    def to_job(self, job_id: str, spark_name: str) -> QuantumJobSpec:
        """Convert landscape to quantum job specification."""
        return QuantumJobSpec(
            job_id=job_id,
            problem_type=QuantumProblemType.OPTIMIZATION,
            variables=self.dimensions,
            couplings=self.tensions,
            biases=self.biases,
            metadata={"spark": spark_name}
        )
