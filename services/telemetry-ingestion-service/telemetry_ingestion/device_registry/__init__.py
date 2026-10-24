"""Device Registry component.

Knows every gateway and device, which farm each belongs to, when each was last
heard from (ONLINE/OFFLINE after 30 minutes, ASR19) and each device's versioned
configuration, which the gateway pushes on the device's next connection (ASR21).
"""

from .models import Device, DeviceConfiguration, DeviceHealth, Gateway
from .repository import InMemoryDeviceRepository, seeded_device_repository
from .service import OFFLINE_AFTER, DeviceRegistryService

__all__ = [
    "OFFLINE_AFTER",
    "Device",
    "DeviceConfiguration",
    "DeviceHealth",
    "DeviceRegistryService",
    "Gateway",
    "InMemoryDeviceRepository",
    "seeded_device_repository",
]
