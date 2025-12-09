"""
Quantum Schemas for TraceOS

Defines core models for quantum-style jobs and results.
Initially powered by classical simulation, but architected
to be replaced or augmented by real quantum backends later.

@provenance traceos_quantum_v1
@organ quantum
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class QuantumProblemType(str, Enum):
    OPTIMIZATION = "OPTIMIZATION"       # Minimize Energy
    PROVENANCE_CHECK = "PROVENANCE_CHECK"
    STYLE_DNA_FIT = "STYLE_DNA_FIT"


class QuantumBackendType(str, Enum):
    CLASSICAL_SIM = "classical-sim"     # Simulated Annealing
    IBM_QUANTUM = "ibm-quantum"         # Future Real Hardware


class QuantumJobSpec(BaseModel):
    """Declarative spec for a quantum job."""
    job_id: str
    problem_type: QuantumProblemType
    variables: List[str]                # Variable names
    # Hamiltonian terms
    couplings: Dict[str, float] = Field(default_factory=dict, description="Pairs 'a|b': weight")
    biases: Dict[str, float] = Field(default_factory=dict, description="Linear 'a': weight")
    metadata: Dict[str, Any] = {}


class QuantumJobResult(BaseModel):
    """Result from the annealing process."""
    job_id: str
    solution: Dict[str, int]            # {var: 1} or {var: -1}
    energy: float                       # Lower is better
    backend: QuantumBackendType
    execution_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
