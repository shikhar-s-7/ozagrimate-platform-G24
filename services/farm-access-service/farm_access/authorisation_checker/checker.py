"""Caller and farm-ownership checks."""

from __future__ import annotations

from ozagrimate_common import ApiError

from ..farm_registry.models import Farm


class AuthorisationChecker:
    def require_caller(self, user_id: str | None) -> str:
        """Return the caller's user ID, or answer 401 when the gateway sent none."""
        if user_id is None or not user_id.strip():
            raise ApiError(
                401,
                "Missing X-User-Id header: the API Gateway sets it after validating the caller's token",
                headers={"WWW-Authenticate": 'Bearer realm="OzAgriMate"'},
            )
        return user_id.strip()

    def require_owner(self, user_id: str, farm: Farm) -> None:
        """Only the farm's owner may share or stop sharing its data (403 otherwise)."""
        if farm.owner_id != user_id:
            raise ApiError(403, f"User {user_id} does not own farm {farm.farm_id}")
