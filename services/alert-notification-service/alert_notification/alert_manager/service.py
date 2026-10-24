"""Alert Manager service: raise alerts, change their status and answer alert queries."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from ozagrimate_common import ApiError

from ..delivery_tracker.tracker import DeliverySummary, DeliveryTracker
from ..farm_access_cache.cache import FarmAccessCache, FarmRecord
from ..rule_manager.models import BELOW_MIN, AlertRule
from .models import Alert, AlertStatus
from .publisher import InMemoryAlertEventPublisher
from .repository import InMemoryAlertRepository


def _number(value: float) -> str:
    return f"{value:g}"


class AlertManager:
    def __init__(
        self,
        *,
        alerts: InMemoryAlertRepository,
        farms: FarmAccessCache,
        tracker: DeliveryTracker,
        publisher: InMemoryAlertEventPublisher,
        clock: Callable[[], datetime],
    ) -> None:
        self._alerts = alerts
        self._farms = farms
        self._tracker = tracker
        self._publisher = publisher
        self._clock = clock

    def raise_alert(
        self, *, farm: FarmRecord, rule: AlertRule, device_id: str, value: float, breach: str, at: datetime
    ) -> Alert | None:
        """Store a new OPEN alert and publish AlertRaised.

        While an alert for the same rule and device is still OPEN, further
        breaches do not raise new alerts, so a farmer is not flooded with
        messages every 15 minutes (ADR-08).
        """
        if self._alerts.find_open(farm.farm_id, rule.rule_id, device_id) is not None:
            return None
        limit = rule.min_value if breach == BELOW_MIN else rule.max_value
        direction = "below the minimum" if breach == BELOW_MIN else "above the maximum"
        alert = Alert(
            alert_id=self._alerts.next_id(),
            farm_id=farm.farm_id,
            rule_id=rule.rule_id,
            device_id=device_id,
            metric=rule.metric,
            value=value,
            unit=rule.unit,
            min_value=rule.min_value,
            max_value=rule.max_value,
            breach=breach,
            severity=rule.severity,
            status=AlertStatus.OPEN.value,
            message=(
                f"{rule.metric} {_number(value)} {rule.unit} on {device_id} is {direction} "
                f"of {_number(limit)} {rule.unit} for {rule.crop_type} in {rule.region}"
            ),
            raised_at=at,
        )
        self._alerts.save(alert)
        self._publisher.alert_raised(alert)
        return alert

    def change_status(self, alert_id: str, status: AlertStatus) -> Alert:
        """The farmer acknowledges an alert, or it is resolved when readings recover."""
        alert = self._alerts.find(alert_id)
        if alert is None:
            raise ApiError(404, f"Alert {alert_id} does not exist")
        alert.status = status.value
        self._alerts.save(alert)
        return alert

    def list_for_farm(
        self, *, caller_id: str | None, farm_id: str, status: AlertStatus | None
    ) -> list[tuple[Alert, DeliverySummary]]:
        """Checks run in this order: 401 caller, 404 farm, 403 no access. Newest alert first."""
        caller = self._farms.require_caller(caller_id)
        farm = self._farms.require_farm(farm_id)
        self._farms.require_alert_access(caller, farm, self._clock())

        alerts = [a for a in self._alerts.for_farm(farm.farm_id) if status is None or a.status == status.value]
        alerts.sort(key=lambda a: (a.raised_at, a.alert_id), reverse=True)
        return [(alert, self._tracker.summary(alert.alert_id)) for alert in alerts]
