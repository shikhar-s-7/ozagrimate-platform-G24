"""Alert & Notification Service: the FastAPI app (port 8082).

Run from the repository root:
    python -m uvicorn alert_notification.main:app --app-dir services/alert-notification-service --port 8082
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from fastapi import FastAPI
from ozagrimate_common import register_error_handlers, utc_now

from .alert_manager.publisher import InMemoryAlertEventPublisher
from .alert_manager.repository import InMemoryAlertRepository
from .alert_manager.service import AlertManager
from .api.alert_routes import router as alert_router
from .api.alert_rule_routes import router as alert_rule_router
from .delivery_tracker.tracker import DeliveryTracker
from .farm_access_cache.cache import seeded_farm_access_cache
from .notification_dispatcher.channels import InMemoryPushService, InMemorySmsGateway
from .notification_dispatcher.dispatcher import NotificationDispatcher
from .rule_manager.repository import seeded_rule_repository
from .rule_manager.service import RuleManager
from .seed import replay_seed_telemetry
from .threshold_evaluator.evaluator import ThresholdEvaluator


def create_app(clock: Callable[[], datetime] = utc_now) -> FastAPI:
    """Build the app and wire its components with fresh in-memory data."""
    app = FastAPI(
        title="OzAgriMate - Alert & Notification Service",
        version="1.0.0",
        description=(
            "Endpoints #4-6: list a farm's alerts, replace an alert rule, delete an alert rule. "
            "The API Gateway sets the X-User-Id header after validating the caller's token."
        ),
    )
    register_error_handlers(app)

    now = clock()
    farms = seeded_farm_access_cache()
    rules = RuleManager(seeded_rule_repository(now), clock=clock)
    tracker = DeliveryTracker()
    events = InMemoryAlertEventPublisher()
    push = InMemoryPushService()
    sms = InMemorySmsGateway()
    alert_manager = AlertManager(
        alerts=InMemoryAlertRepository(), farms=farms, tracker=tracker, publisher=events, clock=clock
    )
    dispatcher = NotificationDispatcher(push=push, sms=sms, tracker=tracker, farms=farms)
    evaluator = ThresholdEvaluator(rules=rules, farms=farms, alerts=alert_manager, dispatcher=dispatcher)
    replay_seed_telemetry(now, evaluator=evaluator, alerts=alert_manager, dispatcher=dispatcher, push=push)

    app.state.farms = farms
    app.state.rules = rules
    app.state.tracker = tracker
    app.state.events = events
    app.state.push = push
    app.state.sms = sms
    app.state.alert_manager = alert_manager
    app.state.dispatcher = dispatcher
    app.state.evaluator = evaluator

    app.include_router(alert_router)
    app.include_router(alert_rule_router)
    return app


app = create_app()
