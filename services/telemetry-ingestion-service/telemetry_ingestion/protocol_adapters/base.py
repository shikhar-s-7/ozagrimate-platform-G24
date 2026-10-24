"""The canonical reading format that every adapter produces (ADR-03)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CanonicalReading:
    """One sensor reading in the platform's single internal format."""

    device_id: str
    sequence_no: int
    metric: str
    value: float
    unit: str
    captured_at: datetime


@dataclass(frozen=True)
class CanonicalBatch:
    """All readings that one gateway sent in one message."""

    gateway_id: str
    readings: tuple[CanonicalReading, ...]
    protocol: str


class MalformedPayload(ValueError):
    """The message cannot be read with this adapter's protocol."""


class ProtocolAdapter(ABC):
    """Target interface of the Adapter pattern: the pipeline only ever sees a CanonicalBatch."""

    protocol: str

    @abstractmethod
    def to_canonical(self, payload: Any) -> CanonicalBatch:
        """Translate one protocol-specific message into a canonical batch."""
