"""Device Registry service: lookups, device health and configuration changes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta

from ozagrimate_common import ApiError

from .models import PENDING_DEVICE_SYNC, Device, DeviceConfiguration, DeviceHealth, Gateway
from .repository import InMemoryDeviceRepository

OFFLINE_AFTER = timedelta(minutes=30)  # ASR19: flag offline devices within 30 minutes


class DeviceRegistryService:
    def __init__(self, repository: InMemoryDeviceRepository, clock: Callable[[], datetime]) -> None:
        self._repository = repository
        self._clock = clock

    def find_gateway(self, gateway_id: str) -> Gateway | None:
        return self._repository.find_gateway(gateway_id)

    def find_device(self, device_id: str) -> Device | None:
        return self._repository.find_device(device_id)

    def require_device(self, device_id: str) -> Device:
        device = self._repository.find_device(device_id)
        if device is None:
            raise ApiError(404, f"Device {device_id} is not registered")
        return device

    def record_contact(self, device_id: str, sequence_no: int, seen_at: datetime) -> None:
        """Mark that the device was heard from, via its gateway, at ``seen_at``."""
        device = self.require_device(device_id)
        device.last_seen_at = seen_at
        if device.last_sequence_no is None or sequence_no > device.last_sequence_no:
            device.last_sequence_no = sequence_no
        self._repository.save_device(device)

    def health(self, device_id: str) -> DeviceHealth:
        device = self.require_device(device_id)
        if device.last_seen_at is None:
            return DeviceHealth(device, "OFFLINE", None, _minutes(OFFLINE_AFTER))
        silent_for = self._clock() - device.last_seen_at
        status = "ONLINE" if silent_for <= OFFLINE_AFTER else "OFFLINE"
        return DeviceHealth(device, status, max(0, _minutes(silent_for)), _minutes(OFFLINE_AFTER))

    def update_configuration(
        self,
        device_id: str,
        *,
        sampling_interval_seconds: int,
        reporting_interval_seconds: int,
        buffer_when_offline: bool,
    ) -> DeviceConfiguration:
        """Replace the configuration as a new version, pending sync to the device.

        PUT is idempotent: sending the configuration the device already has
        changes nothing and returns the current version.
        """
        device = self.require_device(device_id)
        current = device.configuration
        if current.same_settings_as(sampling_interval_seconds, reporting_interval_seconds, buffer_when_offline):
            return current
        device.configuration = replace(
            current,
            sampling_interval_seconds=sampling_interval_seconds,
            reporting_interval_seconds=reporting_interval_seconds,
            buffer_when_offline=buffer_when_offline,
            version=current.version + 1,
            sync_status=PENDING_DEVICE_SYNC,
            updated_at=self._clock(),
        )
        self._repository.save_device(device)
        return device.configuration


def _minutes(duration: timedelta) -> int:
    return int(duration.total_seconds() // 60)
