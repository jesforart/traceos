"""
TraceOS Quantum Organ

Quantum-style energy minimization for emotional and constraint landscapes.

@provenance traceos_quantum_v1
@organ quantum
"""

from .schemas import (
    QuantumProblemType,
    QuantumBackendType,
    QuantumJobSpec,
    QuantumJobResult
)
from .landscape import EnergyLandscape
from .coprocessor import QuantumCoProcessor
from .classical_backend import ClassicalSimCoprocessor
from .jobs import QuantumJobStore

__all__ = [
    "QuantumProblemType",
    "QuantumBackendType",
    "QuantumJobSpec",
    "QuantumJobResult",
    "EnergyLandscape",
    "QuantumCoProcessor",
    "ClassicalSimCoprocessor",
    "QuantumJobStore"
]
