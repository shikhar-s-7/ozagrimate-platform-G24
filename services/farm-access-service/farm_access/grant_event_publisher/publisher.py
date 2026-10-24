"""In-memory stand-in for the Kafka producer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..grant_manager.models import AccessGrant

ACCESS_TOPIC = "access.grants"


@dataclass(frozen=True)
class PublishedEvent:
    topic: str
    key: str
    payload: dict[str, Any]


def _iso(moment: datetime | None) -> str | None:
    return None if moment is None else moment.isoformat().replace("+00:00", "Z")


class InMemoryGrantEventPublisher:
    def __init__(self) -> None:
        self.published: list[PublishedEvent] = []

    def access_granted(self, grant: AccessGrant) -> PublishedEvent:
        return self._publish(
            grant,
            {
                "eventType": "AccessGranted",
                "schemaVersion": 1,
                "grantId": grant.grant_id,
                "farmId": grant.farm_id,
                "agronomistId": grant.agronomist_id,
                "scopes": list(grant.scopes),
                "grantedBy": grant.granted_by,
                "grantedAt": _iso(grant.granted_at),
                "expiresAt": _iso(grant.expires_at),
            },
        )

    def access_revoked(self, grant: AccessGrant) -> PublishedEvent:
        return self._publish(
            grant,
            {
                "eventType": "AccessRevoked",
                "schemaVersion": 1,
                "grantId": grant.grant_id,
                "farmId": grant.farm_id,
                "agronomistId": grant.agronomist_id,
                "revokedBy": grant.revoked_by,
                "revokedAt": _iso(grant.revoked_at),
            },
        )

    def _publish(self, grant: AccessGrant, payload: dict[str, Any]) -> PublishedEvent:
        event = PublishedEvent(topic=ACCESS_TOPIC, key=grant.farm_id, payload=payload)
        self.published.append(event)
        return event
