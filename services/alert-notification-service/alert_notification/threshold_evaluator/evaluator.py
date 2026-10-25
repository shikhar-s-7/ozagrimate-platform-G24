"""Checks each reading in a TelemetryReceived event against the farm's alert rules."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..alert_manager.models import Alert
from ..alert_manager.service import AlertManager
from ..farm_access_cache.cache import FarmAccessCache
from ..notification_dispatcher.dispatcher import NotificationDispatcher
from ..rule_manager.service import RuleManager


class ThresholdEvaluator:
    def __init__(
        self,
        *,
        rules: RuleManager,
        farms: FarmAccessCache,
        alerts: AlertManager,
        dispatcher: NotificationDispatcher,
    ) -> None:
        self._rules = rules
        self._farms = farms
        self._alerts = alerts
        self._dispatcher = dispatcher

    def on_telemetry_received(self, payload: dict[str, Any]) -> list[Alert]:
        """Consume one event from the telemetry.received topic; return the alerts it raised.

        No threshold is written here: every limit comes from a rule, so a new
        crop or region needs data, not code (ADR-08 compliance).
        """
        farm = self._farms.find_farm(payload["farmId"])
        if farm is None:
            return []
        received_at = datetime.fromisoformat(payload["receivedAt"].replace("Z", "+00:00"))
        raised = []
        for reading in payload["readings"]:
            for rule in self._rules.rules_for(farm.crop_type, farm.region, reading["metric"]):
                breach = rule.breach(reading["value"])
                if breach is None:
                    continue
                alert = self._alerts.raise_alert(
                    farm=farm, rule=rule, device_id=reading["deviceId"], value=reading["value"], breach=breach, at=received_at
                )
                if alert is not None:
                    self._dispatcher.dispatch(alert, received_at)
                    raised.append(alert)
        return raised
