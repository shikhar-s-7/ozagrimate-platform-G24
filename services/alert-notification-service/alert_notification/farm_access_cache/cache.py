"""Local copy of farms and access grants, and the read-access check for alerts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ozagrimate_common import ApiError

READ_ALERTS = "READ_ALERTS"


@dataclass(frozen=True)
class FarmRecord:
    farm_id: str
    owner_id: str
    owner_phone: str
    crop_type: str
    region: str


@dataclass(frozen=True)
class GrantRecord:
    grant_id: str
    farm_id: str
    agronomist_id: str
    scopes: tuple[str, ...]
    expires_at: datetime | None

    def allows_alerts(self, now: datetime) -> bool:
        return READ_ALERTS in self.scopes and (self.expires_at is None or self.expires_at > now)


def _parse_time(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value.replace("Z", "+00:00"))


class FarmAccessCache:
    def __init__(self, farms: Iterable[FarmRecord]) -> None:
        self._farms = {farm.farm_id: farm for farm in farms}
        self._grants: dict[str, GrantRecord] = {}

    # ----- kept in step by events from the Farm & Access Service -----

    def apply_access_event(self, payload: dict[str, Any]) -> None:
        """Consume AccessGranted / AccessRevoked from the access.grants topic."""
        if payload["eventType"] == "AccessGranted":
            self._grants[payload["grantId"]] = GrantRecord(
                grant_id=payload["grantId"],
                farm_id=payload["farmId"],
                agronomist_id=payload["agronomistId"],
                scopes=tuple(payload["scopes"]),
                expires_at=_parse_time(payload.get("expiresAt")),
            )
        elif payload["eventType"] == "AccessRevoked":
            self._grants.pop(payload["grantId"], None)

    # ----- lookups and checks -----

    def find_farm(self, farm_id: str) -> FarmRecord | None:
        return self._farms.get(farm_id)

    def require_farm(self, farm_id: str) -> FarmRecord:
        farm = self._farms.get(farm_id)
        if farm is None:
            raise ApiError(404, f"Farm {farm_id} does not exist")
        return farm

    def require_caller(self, user_id: str | None) -> str:
        """Return the caller's user ID, or answer 401 when the gateway sent none."""
        if user_id is None or not user_id.strip():
            raise ApiError(
                401,
                "Missing X-User-Id header: the API Gateway sets it after validating the caller's token",
                headers={"WWW-Authenticate": 'Bearer realm="OzAgriMate"'},
            )
        return user_id.strip()

    def require_alert_access(self, user_id: str, farm: FarmRecord, now: datetime) -> None:
        """The owner, or an agronomist with an active READ_ALERTS grant, may read a farm's alerts (ASR9)."""
        if farm.owner_id == user_id:
            return
        for grant in self._grants.values():
            if grant.farm_id == farm.farm_id and grant.agronomist_id == user_id and grant.allows_alerts(now):
                return
        raise ApiError(403, f"User {user_id} has no access to the alerts of farm {farm.farm_id}")


def seeded_farm_access_cache() -> FarmAccessCache:
    """The same farms and GRANT-001 as the Farm & Access Service seeds."""
    cache = FarmAccessCache(
        [
            FarmRecord("FARM-001", "FARMER-001", "+61400000001", "WHEAT", "RIVERINA-NSW"),
            FarmRecord("FARM-002", "FARMER-002", "+61400000002", "ALMONDS", "RIVERLAND-SA"),
        ]
    )
    cache.apply_access_event(
        {
            "eventType": "AccessGranted",
            "schemaVersion": 1,
            "grantId": "GRANT-001",
            "farmId": "FARM-001",
            "agronomistId": "AGR-002",
            "scopes": ["READ_TELEMETRY", "READ_ALERTS"],
            "expiresAt": None,
        }
    )
    return cache
