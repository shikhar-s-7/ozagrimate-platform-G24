"""In-memory stand-in for the access-grant table, with seed data."""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from datetime import datetime, timedelta

from .models import ACTIVE, AccessGrant


class InMemoryGrantRepository:
    def __init__(self, grants: Iterable[AccessGrant]) -> None:
        self._grants = {grant.grant_id: grant for grant in grants}
        self._numbers = itertools.count(len(self._grants) + 1)

    def next_id(self) -> str:
        return f"GRANT-{next(self._numbers):03d}"

    def save(self, grant: AccessGrant) -> None:
        self._grants[grant.grant_id] = grant

    def find(self, grant_id: str) -> AccessGrant | None:
        return self._grants.get(grant_id)

    def find_active(self, farm_id: str, agronomist_id: str, now: datetime) -> AccessGrant | None:
        for grant in self._grants.values():
            if grant.farm_id == farm_id and grant.agronomist_id == agronomist_id and grant.is_active(now):
                return grant
        return None


def seeded_grant_repository(now: datetime) -> InMemoryGrantRepository:
    """GRANT-001: FARMER-001 already shares FARM-001 with AGR-002."""
    return InMemoryGrantRepository(
        [
            AccessGrant(
                grant_id="GRANT-001",
                farm_id="FARM-001",
                agronomist_id="AGR-002",
                agronomist_name="Coastal Crop Advisory",
                scopes=("READ_TELEMETRY", "READ_ALERTS"),
                status=ACTIVE,
                granted_by="FARMER-001",
                granted_at=now - timedelta(days=30),
            )
        ]
    )
