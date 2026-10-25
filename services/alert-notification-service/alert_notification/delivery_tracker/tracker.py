"""Delivery records for every notification attempt, and the push-to-SMS timeout."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

PUSH = "PUSH"
SMS = "SMS"
SENT = "SENT"
DELIVERED = "DELIVERED"
FAILED = "FAILED"

# ADR-04: if a push is not confirmed within 2 minutes, fall back to SMS. This
# keeps the whole alert inside the 5-minute budget of ASR2.
PUSH_CONFIRMATION_WINDOW = timedelta(minutes=2)


@dataclass
class DeliveryAttempt:
    alert_id: str
    channel: str
    attempt_no: int
    status: str
    sent_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DeliverySummary:
    status: str
    attempts: int


class DeliveryTracker:
    def __init__(self) -> None:
        self._attempts: dict[str, list[DeliveryAttempt]] = {}

    def record(self, alert_id: str, channel: str, status: str, at: datetime) -> DeliveryAttempt:
        attempts = self._attempts.setdefault(alert_id, [])
        attempt = DeliveryAttempt(alert_id, channel, len(attempts) + 1, status, at, at)
        attempts.append(attempt)
        return attempt

    def mark_delivered(self, attempt: DeliveryAttempt, at: datetime) -> None:
        """Called when the push service or SMS gateway confirms delivery."""
        attempt.status = DELIVERED
        attempt.updated_at = at

    def attempts(self, alert_id: str) -> list[DeliveryAttempt]:
        return list(self._attempts.get(alert_id, []))

    def awaiting_sms_fallback(self, now: datetime) -> list[str]:
        """Alerts whose push is still unconfirmed after the window and that have no SMS yet."""
        overdue = []
        for alert_id, attempts in self._attempts.items():
            pushes = [a for a in attempts if a.channel == PUSH]
            if not pushes or any(a.channel == SMS for a in attempts):
                continue
            if all(a.status != DELIVERED for a in pushes) and now - pushes[0].sent_at >= PUSH_CONFIRMATION_WINDOW:
                overdue.append(alert_id)
        return overdue

    def summary(self, alert_id: str) -> DeliverySummary:
        """The latest attempt's channel and status, for example SMS_DELIVERED."""
        attempts = self._attempts.get(alert_id, [])
        if not attempts:
            return DeliverySummary("NOT_SENT", 0)
        latest = attempts[-1]
        return DeliverySummary(f"{latest.channel}_{latest.status}", len(attempts))
