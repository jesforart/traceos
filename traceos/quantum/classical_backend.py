"""
Classical Simulation Backend for Quantum Jobs

Implements lightweight energy minimization using simulated annealing.
This is not true quantum computation; it is a "quantum-shaped" classical
metabolism that can later be swapped for real hardware.

@provenance traceos_quantum_v1
@organ quantum
"""

import random
import math
import asyncio
import logging
from datetime import datetime
from typing import Dict

from .coprocessor import QuantumCoProcessor
from .schemas import QuantumJobSpec, QuantumJobResult, QuantumBackendType

logger = logging.getLogger(__name__)


class ClassicalSimCoprocessor(QuantumCoProcessor):
    """Simulated Annealing solver mimicking Quantum Tunneling."""

    async def submit_job(self, spec: QuantumJobSpec) -> QuantumJobResult:
        """
        Submit quantum job for classical simulation.

        Uses simulated annealing to minimize energy landscape.
        Runs in thread pool to avoid blocking main loop.
        """
        logger.info(f"Quantum job {spec.job_id} submitted (classical simulation)")

        # Offload to thread to avoid blocking main loop
        result = await asyncio.to_thread(self._run_annealing, spec)

        logger.info(f"Quantum job {spec.job_id} complete: energy={result.energy:.3f}")
        return result

    def _run_annealing(self, spec: QuantumJobSpec) -> QuantumJobResult:
        """
        Run simulated annealing optimization.

        Uses Metropolis criterion for state transitions.
        """
        start = datetime.now()

        # Random initialization (-1 or 1 for Ising spins)
        state = {v: random.choice([-1, 1]) for v in spec.variables}
        current_energy = self._energy(state, spec)

        # Annealing Loop
        temp = 10.0  # Initial temperature
        for iteration in range(200):
            # Randomly flip one variable
            var = random.choice(spec.variables)
            new_state = state.copy()
            new_state[var] *= -1
            new_energy = self._energy(new_state, spec)

            delta = new_energy - current_energy

            # Metropolis Criterion
            if delta < 0 or random.random() < math.exp(-delta / temp):
                state = new_state
                current_energy = new_energy

            # Cool down
            temp *= 0.95

        duration = (datetime.now() - start).total_seconds() * 1000

        return QuantumJobResult(
            job_id=spec.job_id,
            solution=state,
            energy=current_energy,
            backend=QuantumBackendType.CLASSICAL_SIM,
            execution_time_ms=duration
        )

    def _energy(self, state: Dict[str, int], spec: QuantumJobSpec) -> float:
        """
        Compute energy of current state.

        H = Σ bias_i * x_i + Σ coupling_ij * x_i * x_j
        """
        # Linear bias terms
        E = sum(spec.biases.get(v, 0) * state[v] for v in state)

        # Quadratic coupling terms
        for pair, weight in spec.couplings.items():
            v1, v2 = pair.split("|")
            E += weight * state.get(v1, 0) * state.get(v2, 0)

        return E
