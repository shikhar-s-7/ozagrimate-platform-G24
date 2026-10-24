"""Grant Manager service: the rules for creating and revoking access grants."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone

from ozagrimate_common import ApiError

from ..authorisation_checker.checker import AuthorisationChecker
from ..farm_registry.service import FarmRegistry
from ..grant_event_publisher.publisher import InMemoryGrantEventPublisher
from .models import ACTIVE, REVOKED, AccessGrant
from .repository import InMemoryGrantRepository


class GrantManager:
    def __init__(
        self,
        *,
        grants: InMemoryGrantRepository,
        farms: FarmRegistry,
        checker: AuthorisationChecker,
        publisher: InMemoryGrantEventPublisher,
        clock: Callable[[], datetime],
    ) -> None:
        self._grants = grants
        self._farms = farms
        self._checker = checker
        self._publisher = publisher
        self._clock = clock

    def create_grant(
        self,
        *,
        caller_id: str | None,
        farm_id: str,
        agronomist_id: str,
        scopes: Sequence[str],
        expires_at: datetime | None,
    ) -> AccessGrant:
        """Checks run in this order: 401 caller, 404 farm, 403 owner, 400 expiry, 404 agronomist, 409 duplicate."""
        caller = self._checker.require_caller(caller_id)
        farm = self._farms.require_farm(farm_id)
        self._checker.require_owner(caller, farm)

        now = self._clock()
        if expires_at is not None:
            expires_at = expires_at.astimezone(timezone.utc)
            if expires_at <= now:
                raise ApiError(400, "expiresAt must be in the future")

        agronomist = self._farms.require_agronomist(agronomist_id)
        existing = self._grants.find_active(farm.farm_id, agronomist.agronomist_id, now)
        if existing is not None:
            raise ApiError(
                409,
                f"Agronomist {agronomist.agronomist_id} already has an active grant "
                f"({existing.grant_id}) on farm {farm.farm_id}",
            )

        grant = AccessGrant(
            grant_id=self._grants.next_id(),
            farm_id=farm.farm_id,
            agronomist_id=agronomist.agronomist_id,
            agronomist_name=agronomist.name,
            scopes=tuple(scopes),
            status=ACTIVE,
            granted_by=caller,
            granted_at=now,
            expires_at=expires_at,
        )
        self._grants.save(grant)
        self._publisher.access_granted(grant)
        return grant

    def revoke_grant(self, *, caller_id: str | None, farm_id: str, grant_id: str) -> AccessGrant:
        """Checks run in this order: 401 caller, 404 farm, 403 owner, 404 no active grant."""
        caller = self._checker.require_caller(caller_id)
        farm = self._farms.require_farm(farm_id)
        self._checker.require_owner(caller, farm)

        now = self._clock()
        grant = self._grants.find(grant_id)
        if grant is None or grant.farm_id != farm.farm_id or not grant.is_active(now):
            raise ApiError(404, f"No active grant {grant_id} on farm {farm.farm_id}")

        grant.status = REVOKED
        grant.revoked_by = caller
        grant.revoked_at = now
        self._grants.save(grant)
        self._publisher.access_revoked(grant)
        return grant
