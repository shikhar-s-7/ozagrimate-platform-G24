"""Access grants and their scopes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

ACTIVE = "ACTIVE"
REVOKED = "REVOKED"


class Scope(str, Enum):
    READ_TELEMETRY = "READ_TELEMETRY"
    READ_ALERTS = "READ_ALERTS"
    READ_RECOMMENDATIONS = "READ_RECOMMENDATIONS"
    READ_REPORTS = "READ_REPORTS"


@dataclass
class AccessGrant:
    grant_id: str
    farm_id: str
    agronomist_id: str
    agronomist_name: str
    scopes: tuple[str, ...]
    status: str
    granted_by: str
    granted_at: datetime
    expires_at: datetime | None = None
    revoked_by: str | None = None
    revoked_at: datetime | None = None

    def is_active(self, now: datetime) -> bool:
        """Active means not revoked and not past its expiry time."""
        return self.status == ACTIVE and (self.expires_at is None or self.expires_at > now)
