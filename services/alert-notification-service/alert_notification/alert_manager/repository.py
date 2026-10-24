"""In-memory stand-in for the alert table in the Alert DB."""

from __future__ import annotations

import itertools

from .models import Alert, AlertStatus


class InMemoryAlertRepository:
    def __init__(self) -> None:
        self._alerts: dict[str, Alert] = {}
        self._numbers = itertools.count(1)

    def next_id(self) -> str:
        return f"ALERT-{next(self._numbers):03d}"

    def save(self, alert: Alert) -> None:
        self._alerts[alert.alert_id] = alert

    def find(self, alert_id: str) -> Alert | None:
        return self._alerts.get(alert_id)

    def find_open(self, farm_id: str, rule_id: str, device_id: str) -> Alert | None:
        for alert in self._alerts.values():
            if (alert.farm_id, alert.rule_id, alert.device_id, alert.status) == (
                farm_id,
                rule_id,
                device_id,
                AlertStatus.OPEN.value,
            ):
                return alert
        return None

    def for_farm(self, farm_id: str) -> list[Alert]:
        return [alert for alert in self._alerts.values() if alert.farm_id == farm_id]
