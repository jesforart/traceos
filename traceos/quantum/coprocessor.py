"""
Quantum CoProcessor Interface

Abstract interface for quantum-style job execution.

@provenance traceos_quantum_v1
@organ quantum
"""

from abc import ABC, abstractmethod
from .schemas import QuantumJobSpec, QuantumJobResult


class QuantumCoProcessor(ABC):
    """
    Base interface for quantum or quantum-like backends.

    Implementations:
    - ClassicalSimCoprocessor (Phase 3)
    - Future: IBMQuantumCoprocessor
    """

    @abstractmethod
    async def submit_job(self, spec: QuantumJobSpec) -> QuantumJobResult:
        """Execute a quantum job and return result."""
        pass
