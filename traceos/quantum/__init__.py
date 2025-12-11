"""
TraceOS Quantum Abstraction Layer

Physics-based emotional regulation through energy landscape minimization.
Internal tensions are represented as Hamiltonians and resolved through
simulated annealing (with provisions for future QAOA hardware).
"""

from traceos.quantum.landscape import EnergyLandscape, Tension

__all__ = ["EnergyLandscape", "Tension"]
