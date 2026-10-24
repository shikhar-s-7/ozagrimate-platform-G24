"""In-memory stand-in for the Kafka producer."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..protocol_adapters.base import CanonicalReading

TELEMETRY_TOPIC = "telemetry.received"


@dataclass(frozen=True)
class PublishedEvent:
    topic: str
    key: str
    payload: dict[str, Any]


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


class InMemoryEventPublisher:
    def __init__(self) -> None:
        self.published: list[PublishedEvent] = []

    def publish_telemetry_received(
        self,
        *,
        batch_id: str,
        farm_id: str,
        gateway_id: str,
        received_at: datetime,
        readings: Sequence[CanonicalReading],
    ) -> PublishedEvent:
        event = PublishedEvent(
            topic=TELEMETRY_TOPIC,
            key=farm_id,  # ADR-02: partition by farm
            payload={
                "eventType": "TelemetryReceived",
                "schemaVersion": 1,
                "batchId": batch_id,
                "farmId": farm_id,
                "gatewayId": gateway_id,
                "receivedAt": _iso(received_at),
                "readings": [
                    {
                        "deviceId": reading.device_id,
                        "sequenceNo": reading.sequence_no,
                        "metric": reading.metric,
                        "value": reading.value,
                        "unit": reading.unit,
                        "capturedAt": _iso(reading.captured_at),
                    }
                    for reading in readings
                ],
            },
        )
        self.published.append(event)
        return event
