"""Adapter for gateways that POST JSON over HTTPS (endpoint #1)."""

from __future__ import annotations

from datetime import timezone
from enum import Enum
from typing import Any

from .base import CanonicalBatch, CanonicalReading, ProtocolAdapter


class HttpsJsonAdapter(ProtocolAdapter):
    """Maps the body of endpoint #1 onto the canonical batch.

    The Telemetry API has already checked the JSON against its Pydantic schema,
    so this adapter only maps fields. It receives ``ReadingBatchRequest.model_dump()``.
    """

    protocol = "https-json"

    def to_canonical(self, payload: dict[str, Any]) -> CanonicalBatch:
        readings = tuple(
            CanonicalReading(
                device_id=item["device_id"],
                sequence_no=item["sequence_no"],
                metric=_as_text(item["metric"]),
                value=float(item["value"]),
                unit=item["unit"],
                captured_at=item["captured_at"].astimezone(timezone.utc),
            )
            for item in payload["readings"]
        )
        return CanonicalBatch(gateway_id=payload["gateway_id"], readings=readings, protocol=self.protocol)


def _as_text(value: Any) -> str:
    return value.value if isinstance(value, Enum) else str(value)
