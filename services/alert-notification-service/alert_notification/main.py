"""Alert & Notification Service: the FastAPI app (port 8082).

Endpoints #4-6 go in alert_notification/api/ (see this service's README).

Run from the repository root:
    python -m uvicorn alert_notification.main:app --app-dir services/alert-notification-service --port 8082
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from fastapi import FastAPI
from ozagrimate_common import register_error_handlers, utc_now

from .api.alert_routes import router as alert_router
from .api.alert_rule_routes import router as alert_rule_router


def create_app(clock: Callable[[], datetime] = utc_now) -> FastAPI:
    """Build the app and wire its components with fresh in-memory data."""
    app = FastAPI(
        title="OzAgriMate - Alert & Notification Service",
        version="1.0.0",
        description="Endpoints #4-6: list a farm's alerts, replace an alert rule, delete an alert rule.",
    )
    register_error_handlers(app)

    # Wire the components here and keep them on app.state, as the other two
    # services do, so each test gets fresh data from create_app(). For example:
    #   rules = RuleManager(seeded_rule_repository(clock()), clock=clock)
    #   app.state.rules = rules

    app.include_router(alert_router)
    app.include_router(alert_rule_router)
    return app


app = create_app()
