"""Gives the routers the components that main.create_app() wired together."""

from fastapi import Request

from ..alert_manager.service import AlertManager
from ..rule_manager.service import RuleManager


def get_alert_manager(request: Request) -> AlertManager:
    return request.app.state.alert_manager


def get_rule_manager(request: Request) -> RuleManager:
    return request.app.state.rules
