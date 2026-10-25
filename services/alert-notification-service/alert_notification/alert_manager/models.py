"""Alerts and their lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


@dataclass
class Alert:
    alert_id: str
    farm_id: str
    rule_id: str
    device_id: str
    metric: str
    value: float
    unit: str
    min_value: float
    max_value: float
    breach: str
    severity: str
    status: str
    message: str
    raised_at: datetime
