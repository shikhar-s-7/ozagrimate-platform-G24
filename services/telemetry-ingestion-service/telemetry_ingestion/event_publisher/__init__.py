"""Event Publisher component.

Publishes one TelemetryReceived event per accepted batch to the Event Broker,
keyed by farmId so each farm's readings stay in order on one partition (ADR-02).
The Alert & Notification and Irrigation Advisory services consume these events.
Here an in-memory outbox stands in for the Kafka producer.
"""

from .publisher import TELEMETRY_TOPIC, InMemoryEventPublisher, PublishedEvent

__all__ = ["TELEMETRY_TOPIC", "InMemoryEventPublisher", "PublishedEvent"]
