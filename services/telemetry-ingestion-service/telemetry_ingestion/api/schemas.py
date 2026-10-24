"""Request and response bodies for endpoints #1-3 (camelCase JSON)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class RequestModel(BaseModel):
    """Incoming JSON: camelCase keys, unknown keys rejected."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ResponseModel(BaseModel):
    """Outgoing JSON: camelCase keys."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Metric(str, Enum):
    SOIL_MOISTURE = "SOIL_MOISTURE"
    SOIL_TEMPERATURE = "SOIL_TEMPERATURE"
    AIR_TEMPERATURE = "AIR_TEMPERATURE"
    RAINFALL = "RAINFALL"
    WATER_FLOW = "WATER_FLOW"


# ----- Endpoint #1: POST /api/v1/telemetry/readings -----

class ReadingIn(RequestModel):
    device_id: str = Field(min_length=1, max_length=64)
    sequence_no: int = Field(ge=0, description="Per-device counter; replays reuse it, so it identifies duplicates.")
    metric: Metric
    value: float
    unit: str = Field(min_length=1, max_length=16, description="Converted to the canonical unit for the metric.")
    captured_at: AwareDatetime


class ReadingBatchRequest(RequestModel):
    gateway_id: str = Field(min_length=1, max_length=64)
    readings: list[ReadingIn] = Field(min_length=1, max_length=500)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "gatewayId": "GW-01",
                    "readings": [
                        {"deviceId": "DEV-1001", "sequenceNo": 101, "metric": "SOIL_MOISTURE", "value": 0.274,
                         "unit": "fraction", "capturedAt": "2026-10-22T08:45:00Z"},
                        {"deviceId": "DEV-1002", "sequenceNo": 57, "metric": "AIR_TEMPERATURE", "value": 75.2,
                         "unit": "F", "capturedAt": "2026-10-22T08:45:00Z"},
                        {"deviceId": "DEV-1002", "sequenceNo": 58, "metric": "RAINFALL", "value": 1.2,
                         "unit": "mm", "capturedAt": "2026-10-22T08:45:00Z"},
                    ],
                }
            ]
        }
    )


class Rejection(ResponseModel):
    index: int
    device_id: str
    sequence_no: int
    reason: str
    message: str


class IngestionAck(ResponseModel):
    batch_id: str
    gateway_id: str
    farm_id: str
    received_at: datetime
    received: int
    accepted: int
    duplicates: int
    rejected: int
    rejections: list[Rejection]


# ----- Endpoint #2: GET /api/v1/devices/{deviceId}/health -----

class DeviceHealthResponse(ResponseModel):
    device_id: str
    farm_id: str
    gateway_id: str
    device_type: str
    status: str
    last_seen_at: datetime | None
    minutes_since_last_seen: int | None
    offline_after_minutes: int
    last_sequence_no: int | None
    configuration_version: int


# ----- Endpoint #3: PUT /api/v1/devices/{deviceId}/configuration -----

class DeviceConfigurationRequest(RequestModel):
    sampling_interval_seconds: int = Field(ge=60, le=3600)
    reporting_interval_seconds: int = Field(ge=60, le=86400)
    buffer_when_offline: bool

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"samplingIntervalSeconds": 300, "reportingIntervalSeconds": 900, "bufferWhenOffline": True}
            ]
        }
    )

    @model_validator(mode="after")
    def reporting_not_shorter_than_sampling(self) -> "DeviceConfigurationRequest":
        if self.reporting_interval_seconds < self.sampling_interval_seconds:
            raise ValueError(
                "reportingIntervalSeconds must be greater than or equal to samplingIntervalSeconds"
            )
        return self


class DeviceConfigurationResponse(ResponseModel):
    device_id: str
    sampling_interval_seconds: int
    reporting_interval_seconds: int
    buffer_when_offline: bool
    version: int
    sync_status: str
    updated_at: datetime
