"""Gives the routers the components that main.create_app() wired together."""

from fastapi import Depends, Header, Request

from ..alert_manager.service import AlertManager
from ..farm_access_cache.cache import FarmAccessCache
from ..rule_manager.service import RuleManager


def get_alert_manager(request: Request) -> AlertManager:
    return request.app.state.alert_manager


def get_rule_manager(request: Request) -> RuleManager:
    return request.app.state.rules


def get_farm_access_cache(request: Request) -> FarmAccessCache:
    return request.app.state.farms


def require_rule_editor(
    user_id: str | None = Header(
        default=None,
        alias="X-User-Id",
        description="Set by the API Gateway after it validates the caller's token (ADR-05).",
        examples=["AGR-001"],
    ),
    role: str | None = Header(
        default=None,
        alias="X-User-Role",
        description=(
            "The caller's role from the token, set by the API Gateway. "
            "AGRONOMIST or OPERATIONS_STAFF may change rules."
        ),
        examples=["AGRONOMIST"],
    ),
    farms: FarmAccessCache = Depends(get_farm_access_cache),
    rules: RuleManager = Depends(get_rule_manager),
) -> str:
    """Runs before the body is validated: 401 without X-User-Id, then 403 for any other role."""
    caller = farms.require_caller(user_id)
    rules.require_editor(caller, role)
    return caller
