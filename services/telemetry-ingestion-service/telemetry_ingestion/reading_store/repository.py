"""In-memory repository for accepted readings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StoredReading:
    batch_id: str
    farm_id: str
    gateway_id: str
    device_id: str
    sequence_no: int
    metric: str
    value: float
    unit: str
    captured_at: datetime
    received_at: datetime


class InMemoryReadingRepository:
    def __init__(self) -> None:
        self._readings: list[StoredReading] = []

    def save(self, reading: StoredReading) -> None:
        self._readings.append(reading)

    def all(self) -> list[StoredReading]:
        return list(self._readings)

    def for_device(self, device_id: str) -> list[StoredReading]:
        return [reading for reading in self._readings if reading.device_id == device_id]

    def count(self) -> int:
        return len(self._readings)
