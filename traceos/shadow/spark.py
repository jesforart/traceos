"""
TraceOS Shadow Spark - Anomaly Detection Organ

Open Source Reference Implementation.

This module provides the interface definition for the Shadow Spark
(anomaly detection system). Full detection pipelines are proprietary.

Canonical Role: AnomalyDetector
System Alias: System Health Monitor

@provenance traceos_shadow_v1
@organ shadow
"""

from typing import List
from traceos.sparks.base import SparkBase
from traceos.sparks.schemas import SparkMetadata


class ShadowSpark(SparkBase):
    """
    Shadow Spark - The Anomaly Detection Organ (Open Source Stub).

    This is a REFERENCE IMPLEMENTATION providing:
        - Interface definitions for anomaly detection
        - Basic structure for evaluation loop compliance
        - No advanced detection pipelines

    The proprietary implementation includes:
        - Input validation detectors
        - Render corruption detectors
        - DNA drift monitoring
        - Behavioral anomaly detection

    Canonical Role: AnomalyDetector
    System Alias: System Health Monitor
    """

    def _define_metadata(self) -> SparkMetadata:
        return SparkMetadata(
            name="Shadow",
            organ_type="identity",  # Acts as immune system
            description="Anomaly detection and integrity assurance",
            version="1.0",
            canonical_role="AnomalyDetector",
            system_alias="System Health Monitor",
        )

    def evaluate(self, derivation) -> dict:
        """
        Evaluate derivation for anomalies.

        STUB: Returns healthy status in reference implementation.
        Production uses full detection pipeline.
        """
        # Basic stub - always reports healthy
        return {
            "spark": "Shadow",
            "status": "approve",
            "score": 1.0,
            "comments": [
                {
                    "severity": "info",
                    "message": "Shadow stub: No anomalies detected (stub implementation)"
                }
            ]
        }

    def get_state(self) -> dict:
        """Return current Shadow state for health checks."""
        return {
            "activation": self.state.activation if hasattr(self, 'state') else 0.5,
            "mood": "dormant",
            "status": "stub_implementation"
        }
