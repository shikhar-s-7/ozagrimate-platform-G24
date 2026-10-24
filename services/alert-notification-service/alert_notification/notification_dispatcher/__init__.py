"""Notification Dispatcher component.

Sends each alert by push notification first and falls back to SMS through the
SMS gateway when the push is not delivered (ADR-04, ASR6, C4). Here in-memory
stand-ins replace the external Push Notification Service and SMS Gateway.
"""

from .channels import InMemoryPushService, InMemorySmsGateway
from .dispatcher import SMS_MAX_ATTEMPTS, NotificationDispatcher

__all__ = ["SMS_MAX_ATTEMPTS", "InMemoryPushService", "InMemorySmsGateway", "NotificationDispatcher"]
