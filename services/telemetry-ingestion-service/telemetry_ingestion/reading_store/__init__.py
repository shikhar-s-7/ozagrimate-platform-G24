"""Reading Store component.

Saves accepted readings. In production this writes to the Telemetry Store
(TimescaleDB) and keeps 24 months of history (ASR4, ADR-07); here an in-memory
list stands in for the database.
"""

from .repository import InMemoryReadingRepository, StoredReading

__all__ = ["InMemoryReadingRepository", "StoredReading"]
