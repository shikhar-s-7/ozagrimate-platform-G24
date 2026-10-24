"""Gives the router the components that main.create_app() wired together."""

from fastapi import Request

from ..grant_manager.service import GrantManager


def get_grant_manager(request: Request) -> GrantManager:
    return request.app.state.grant_manager
