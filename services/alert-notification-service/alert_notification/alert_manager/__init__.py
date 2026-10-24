"""Alert Manager component.

Raises, stores and updates alerts for each farm, publishes AlertRaised to the
Event Broker, and answers alert queries (endpoint #4). In production it reads
the Alert DB (PostgreSQL); here an in-memory repository stands in for it.
"""

from .models import Alert, AlertStatus
from .publisher import ALERTS_TOPIC, InMemoryAlertEventPublisher, PublishedEvent
from .repository import InMemoryAlertRepository
from .service import AlertManager

__all__ = [
    "ALERTS_TOPIC",
    "Alert",
    "AlertManager",
    "AlertStatus",
    "InMemoryAlertEventPublisher",
    "InMemoryAlertRepository",
    "PublishedEvent",
]
