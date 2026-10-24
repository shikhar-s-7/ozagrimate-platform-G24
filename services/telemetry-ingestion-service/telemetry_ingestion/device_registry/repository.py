"""In-memory stand-in for the device tables in the Telemetry Store, with seed data."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from .models import IN_SYNC, Device, DeviceConfiguration, Gateway


class InMemoryDeviceRepository:
    def __init__(self, gateways: Iterable[Gateway], devices: Iterable[Device]) -> None:
        self._gateways = {gateway.gateway_id: gateway for gateway in gateways}
        self._devices = {device.device_id: device for device in devices}

    def find_gateway(self, gateway_id: str) -> Gateway | None:
        return self._gateways.get(gateway_id)

    def find_device(self, device_id: str) -> Device | None:
        return self._devices.get(device_id)

    def save_device(self, device: Device) -> None:
        self._devices[device.device_id] = device


def seeded_device_repository(now: datetime) -> InMemoryDeviceRepository:
    """Seed data, with last-contact times relative to start-up.

    DEV-1001 and DEV-1002 start ONLINE; DEV-2001 was last heard from two hours
    ago, so it starts OFFLINE.
    """

    def config(sampling: int, reporting: int) -> DeviceConfiguration:
        return DeviceConfiguration(
            sampling_interval_seconds=sampling,
            reporting_interval_seconds=reporting,
            buffer_when_offline=True,
            version=1,
            sync_status=IN_SYNC,
            updated_at=now - timedelta(days=30),
        )

    gateways = [Gateway("GW-01", "FARM-001"), Gateway("GW-02", "FARM-002")]
    devices = [
        Device("DEV-1001", "FARM-001", "GW-01", "SOIL_MOISTURE_PROBE", now - timedelta(minutes=5), 100, config(600, 1800)),
        Device("DEV-1002", "FARM-001", "GW-01", "WEATHER_STATION", now - timedelta(minutes=3), 56, config(300, 900)),
        Device("DEV-2001", "FARM-002", "GW-02", "WATER_FLOW_METER", now - timedelta(minutes=120), 880, config(60, 300)),
    ]
    return InMemoryDeviceRepository(gateways, devices)
