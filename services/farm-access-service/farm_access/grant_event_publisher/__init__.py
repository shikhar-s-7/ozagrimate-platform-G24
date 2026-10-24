"""Grant Event Publisher component.

Publishes AccessGranted and AccessRevoked events to the Event Broker, keyed by
farmId (ADR-02). The Alert & Notification Service consumes them, so an
agronomist starts or stops receiving a farm's alerts as soon as access changes.
Here an in-memory outbox stands in for the Kafka producer.
"""

from .publisher import ACCESS_TOPIC, InMemoryGrantEventPublisher, PublishedEvent

__all__ = ["ACCESS_TOPIC", "InMemoryGrantEventPublisher", "PublishedEvent"]
