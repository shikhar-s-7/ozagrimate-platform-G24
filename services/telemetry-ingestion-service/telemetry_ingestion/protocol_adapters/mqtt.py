"""Adapter for gateways that publish compact JSON over MQTT.

Topic:   farms/{farmId}/gateways/{gatewayId}/telemetry
Payload: {"r": [[deviceId, sequenceNo, metric, value, unit, capturedAtEpochSeconds], ...]}

Rows instead of objects keep messages small on low-bandwidth rural links (C5).
The MQTT broker is outside this prototype, so this adapter is exercised by unit
tests only. It shows a second protocol plugging in without any change to the
ingestion pipeline (ASR26).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from .base import CanonicalBatch, CanonicalReading, MalformedPayload, ProtocolAdapter

TOPIC = re.compile(r"^farms/(?P<farm_id>[^/]+)/gateways/(?P<gateway_id>[^/]+)/telemetry$")


@dataclass(frozen=True)
class MqttMessage:
    topic: str
    payload: bytes


class MqttAdapter(ProtocolAdapter):
    protocol = "mqtt"

    def to_canonical(self, message: MqttMessage) -> CanonicalBatch:
        match = TOPIC.match(message.topic)
        if match is None:
            raise MalformedPayload(
                f"Topic '{message.topic}' does not match farms/{{farmId}}/gateways/{{gatewayId}}/telemetry"
            )
        try:
            rows = json.loads(message.payload)["r"]
            readings = tuple(
                CanonicalReading(
                    device_id=str(device_id),
                    sequence_no=int(sequence_no),
                    metric=str(metric),
                    value=float(value),
                    unit=str(unit),
                    captured_at=datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc),
                )
                for device_id, sequence_no, metric, value, unit, epoch_seconds in rows
            )
        except (ValueError, KeyError, TypeError, OverflowError, OSError) as exc:
            raise MalformedPayload(f"MQTT payload is not valid compact telemetry: {exc}") from exc
        if not readings:
            raise MalformedPayload("MQTT payload contains no readings")
        return CanonicalBatch(gateway_id=match["gateway_id"], readings=readings, protocol=self.protocol)
