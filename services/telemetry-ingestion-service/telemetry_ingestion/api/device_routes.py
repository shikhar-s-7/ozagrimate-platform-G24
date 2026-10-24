"""Endpoints #2 and #3: device health and device configuration."""

from fastapi import APIRouter, Depends, Path
from ozagrimate_common import ErrorBody

from ..device_registry.service import DeviceRegistryService
from .dependencies import get_devices
from .schemas import DeviceConfigurationRequest, DeviceConfigurationResponse, DeviceHealthResponse

router = APIRouter(prefix="/api/v1/devices", tags=["Telemetry API"])


@router.get(
    "/{deviceId}/health",
    response_model=DeviceHealthResponse,
    summary="Return a device's online status and last contact",
    responses={404: {"model": ErrorBody, "description": "Unknown device"}},
)
def get_device_health(
    device_id: str = Path(alias="deviceId", examples=["DEV-1001"]),
    devices: DeviceRegistryService = Depends(get_devices),
) -> DeviceHealthResponse:
    """ONLINE when the device was heard from in the last 30 minutes, otherwise OFFLINE (ASR19)."""
    health = devices.health(device_id)
    device = health.device
    return DeviceHealthResponse(
        device_id=device.device_id,
        farm_id=device.farm_id,
        gateway_id=device.gateway_id,
        device_type=device.device_type,
        status=health.status,
        last_seen_at=device.last_seen_at,
        minutes_since_last_seen=health.minutes_since_last_seen,
        offline_after_minutes=health.offline_after_minutes,
        last_sequence_no=device.last_sequence_no,
        configuration_version=device.configuration.version,
    )


@router.put(
    "/{deviceId}/configuration",
    response_model=DeviceConfigurationResponse,
    summary="Replace a device's sampling and reporting configuration",
    responses={
        400: {"model": ErrorBody, "description": "Interval out of range"},
        404: {"model": ErrorBody, "description": "Unknown device"},
    },
)
def update_device_configuration(
    body: DeviceConfigurationRequest,
    device_id: str = Path(alias="deviceId", examples=["DEV-1001"]),
    devices: DeviceRegistryService = Depends(get_devices),
) -> DeviceConfigurationResponse:
    """Store the new configuration as a new version; the gateway pushes it on the
    device's next connection, so it is PENDING_DEVICE_SYNC until then (ASR21)."""
    configuration = devices.update_configuration(
        device_id,
        sampling_interval_seconds=body.sampling_interval_seconds,
        reporting_interval_seconds=body.reporting_interval_seconds,
        buffer_when_offline=body.buffer_when_offline,
    )
    return DeviceConfigurationResponse(
        device_id=device_id,
        sampling_interval_seconds=configuration.sampling_interval_seconds,
        reporting_interval_seconds=configuration.reporting_interval_seconds,
        buffer_when_offline=configuration.buffer_when_offline,
        version=configuration.version,
        sync_status=configuration.sync_status,
        updated_at=configuration.updated_at,
    )
