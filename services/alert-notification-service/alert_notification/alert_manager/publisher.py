"""In-memory stand-in for the Kafka producer of AlertRaised events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Alert

ALERTS_TOPIC = "alerts.raised"


@dataclass(frozen=True)
class PublishedEvent:
    topic: str
    key: str
    payload: dict[str, Any]


class InMemoryAlertEventPublisher:
    def __init__(self) -> None:
        self.published: list[PublishedEvent] = []

    def alert_raised(self, alert: Alert) -> PublishedEvent:
        event = PublishedEvent(
            topic=ALERTS_TOPIC,
            key=alert.farm_id,  # ADR-02: every topic is keyed by farm
            payload={
                "eventType": "AlertRaised",
                "schemaVersion": 1,
                "alertId": alert.alert_id,
                "farmId": alert.farm_id,
                "ruleId": alert.rule_id,
                "deviceId": alert.device_id,
                "metric": alert.metric,
                "value": alert.value,
                "unit": alert.unit,
                "breach": alert.breach,
                "severity": alert.severity,
                "raisedAt": alert.raised_at.isoformat().replace("+00:00", "Z"),
            },
        )
        self.published.append(event)
        return event
