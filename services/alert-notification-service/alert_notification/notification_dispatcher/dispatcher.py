"""Push first, SMS when the push is not confirmed (ADR-04)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ..delivery_tracker.tracker import FAILED, PUSH, SENT, SMS, DeliveryTracker
from ..farm_access_cache.cache import FarmAccessCache
from .channels import InMemoryPushService, InMemorySmsGateway

if TYPE_CHECKING:
    from ..alert_manager.models import Alert

SMS_MAX_ATTEMPTS = 3


class NotificationDispatcher:
    def __init__(
        self,
        *,
        push: InMemoryPushService,
        sms: InMemorySmsGateway,
        tracker: DeliveryTracker,
        farms: FarmAccessCache,
    ) -> None:
        self._push = push
        self._sms = sms
        self._tracker = tracker
        self._farms = farms
        self._pending: dict[str, Alert] = {}

    def dispatch(self, alert: Alert, at: datetime) -> None:
        """Send the alert to the farm owner's phone as a push notification."""
        farm = self._farms.require_farm(alert.farm_id)
        attempt = self._tracker.record(alert.alert_id, PUSH, SENT, at)
        if self._push.send(farm.owner_id, alert.message):
            self._tracker.mark_delivered(attempt, at)
        else:
            self._pending[alert.alert_id] = alert

    def fall_back_to_sms(self, now: datetime) -> list[str]:
        """Run every 30 seconds in production: text every alert whose push is overdue.

        The SMS is retried up to three times if the provider fails (ADR-04, C4).
        Returns the IDs of the alerts that were texted.
        """
        texted = []
        for alert_id in self._tracker.awaiting_sms_fallback(now):
            alert = self._pending.pop(alert_id)
            farm = self._farms.require_farm(alert.farm_id)
            for _ in range(SMS_MAX_ATTEMPTS):
                attempt = self._tracker.record(alert_id, SMS, SENT, now)
                if self._sms.send(farm.owner_phone, alert.message):
                    self._tracker.mark_delivered(attempt, now)
                    texted.append(alert_id)
                    break
                attempt.status = FAILED
        return texted
