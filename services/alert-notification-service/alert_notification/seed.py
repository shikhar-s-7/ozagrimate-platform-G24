"""Start-up data: replays four TelemetryReceived events through the real components.

The seeded alerts are therefore produced the same way as live ones: Threshold
Evaluator -> Alert Manager -> Notification Dispatcher -> Delivery Tracker.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .alert_manager.models import AlertStatus
from .alert_manager.service import AlertManager
from .delivery_tracker.tracker import PUSH_CONFIRMATION_WINDOW
from .notification_dispatcher.channels import InMemoryPushService
from .notification_dispatcher.dispatcher import NotificationDispatcher
from .threshold_evaluator.evaluator import ThresholdEvaluator


def _event(farm_id: str, gateway_id: str, received_at: datetime, reading: dict) -> dict:
    stamp = received_at.isoformat().replace("+00:00", "Z")
    return {
        "eventType": "TelemetryReceived",
        "schemaVersion": 1,
        "farmId": farm_id,
        "gatewayId": gateway_id,
        "receivedAt": stamp,
        "readings": [{**reading, "capturedAt": stamp}],
    }


def replay_seed_telemetry(
    now: datetime,
    *,
    evaluator: ThresholdEvaluator,
    alerts: AlertManager,
    dispatcher: NotificationDispatcher,
    push: InMemoryPushService,
) -> None:
    """ALERT-001 RESOLVED, ALERT-002 ACKNOWLEDGED, ALERT-003 OPEN on FARM-001 (push missed, SMS sent);
    ALERT-004 OPEN on FARM-002 (push delivered)."""
    # (received, farm, gateway, reading, phone unreachable?, what the farmer did afterwards)
    history = [
        (now - timedelta(days=1), "FARM-001", "GW-01",
         {"deviceId": "DEV-1001", "sequenceNo": 12, "metric": "SOIL_MOISTURE", "value": 47.5, "unit": "%"},
         False, AlertStatus.RESOLVED),
        (now - timedelta(hours=3), "FARM-001", "GW-01",
         {"deviceId": "DEV-1002", "sequenceNo": 40, "metric": "AIR_TEMPERATURE", "value": 39.4, "unit": "C"},
         False, AlertStatus.ACKNOWLEDGED),
        (now - timedelta(minutes=50), "FARM-001", "GW-01",
         {"deviceId": "DEV-1001", "sequenceNo": 99, "metric": "SOIL_MOISTURE", "value": 14.2, "unit": "%"},
         True, None),
        (now - timedelta(minutes=20), "FARM-002", "GW-02",
         {"deviceId": "DEV-2001", "sequenceNo": 7, "metric": "WATER_FLOW", "value": 520.0, "unit": "L/min"},
         False, None),
    ]
    for received_at, farm_id, gateway_id, reading, phone_unreachable, later_status in history:
        push.unreachable_users = {"FARMER-001", "FARMER-002"} if phone_unreachable else set()
        raised = evaluator.on_telemetry_received(_event(farm_id, gateway_id, received_at, reading))
        dispatcher.fall_back_to_sms(received_at + PUSH_CONFIRMATION_WINDOW)
        if later_status is not None:
            for alert in raised:
                alerts.change_status(alert.alert_id, later_status)
    push.unreachable_users = set()
