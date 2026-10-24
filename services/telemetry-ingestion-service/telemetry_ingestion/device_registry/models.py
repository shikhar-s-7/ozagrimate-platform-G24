"""Gateways, devices and device configuration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

IN_SYNC = "IN_SYNC"
PENDING_DEVICE_SYNC = "PENDING_DEVICE_SYNC"


@dataclass(frozen=True)
class Gateway:
    gateway_id: str
    farm_id: str


@dataclass(frozen=True)
class DeviceConfiguration:
    sampling_interval_seconds: int
    reporting_interval_seconds: int
    buffer_when_offline: bool
    version: int
    sync_status: str
    updated_at: datetime

    def same_settings_as(self, sampling: int, reporting: int, buffer_when_offline: bool) -> bool:
        return (
            self.sampling_interval_seconds == sampling
            and self.reporting_interval_seconds == reporting
            and self.buffer_when_offline == buffer_when_offline
        )


@dataclass
class Device:
    device_id: str
    farm_id: str
    gateway_id: str
    device_type: str
    last_seen_at: datetime | None
    last_sequence_no: int | None
    configuration: DeviceConfiguration


@dataclass(frozen=True)
class DeviceHealth:
    device: Device
    status: str
    minutes_since_last_seen: int | None
    offline_after_minutes: int
