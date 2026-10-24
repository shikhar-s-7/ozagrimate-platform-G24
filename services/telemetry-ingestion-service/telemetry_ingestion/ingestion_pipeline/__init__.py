"""Ingestion Pipeline component.

Runs each batch through the other components in a fixed order: protocol adapter,
gateway check, then per reading the device check, duplicate filter, validator and
reading store; finally it records device contact and publishes one event.
It holds no state of its own, so ingestion instances can scale out (ADR-02).
"""

from .pipeline import IngestionPipeline, IngestionResult, RejectionRecord

__all__ = ["IngestionPipeline", "IngestionResult", "RejectionRecord"]
