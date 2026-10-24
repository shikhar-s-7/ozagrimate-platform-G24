"""In-memory stand-ins for the external Push Notification Service and SMS Gateway."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InMemoryPushService:
    """Stands in for APNs/FCM. A push to an unreachable phone is accepted but never confirmed."""

    unreachable_users: set[str] = field(default_factory=set)
    sent: list[tuple[str, str]] = field(default_factory=list)

    def send(self, user_id: str, text: str) -> bool:
        """Send a push; return True when the phone confirms delivery."""
        self.sent.append((user_id, text))
        return user_id not in self.unreachable_users


@dataclass
class InMemorySmsGateway:
    """Stands in for the SMS provider's HTTPS API. ``failures_left`` simulates provider errors."""

    failures_left: int = 0
    sent: list[tuple[str, str]] = field(default_factory=list)

    def send(self, phone: str, text: str) -> bool:
        """Send an SMS; return True when the provider accepts and delivers it."""
        if self.failures_left > 0:
            self.failures_left -= 1
            return False
        self.sent.append((phone, text))
        return True
