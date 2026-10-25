"""Request and response bodies for endpoints #4-6 (camelCase JSON)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from ..alert_manager.models import AlertStatus
from ..rule_manager.models import Metric, Severity

CODE_PATTERN = r"^[A-Z][A-Z0-9-]*$"


class RequestModel(BaseModel):
    """Incoming JSON: camelCase keys, unknown keys rejected."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ResponseModel(BaseModel):
    """Outgoing JSON: camelCase keys."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ----- Endpoint #4: GET /api/v1/farms/{farmId}/alerts?status=OPEN -----

class AlertResponse(ResponseModel):
    alert_id: str
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
    delivery_status: str = Field(description="Latest attempt, for example PUSH_DELIVERED or SMS_DELIVERED (ADR-04).")
    delivery_attempts: int


class FarmAlertsResponse(ResponseModel):
    farm_id: str
    status: AlertStatus | None = Field(description="The status filter, or null when every alert is listed.")
    count: int
    alerts: list[AlertResponse]


# ----- Endpoints #5 and #6: /api/v1/alert-rules/{ruleId} -----

class AlertRuleRequest(RequestModel):
    crop_type: str = Field(min_length=1, max_length=40, pattern=CODE_PATTERN, description="Upper-case code, for example WHEAT.")
    region: str = Field(min_length=1, max_length=40, pattern=CODE_PATTERN, description="Upper-case code, for example RIVERINA-NSW.")
    metric: Metric
    min_value: float = Field(description="In the metric's canonical unit (SOIL_MOISTURE in %).")
    max_value: float
    severity: Severity

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "cropType": "WHEAT",
                    "region": "RIVERINA-NSW",
                    "metric": "SOIL_MOISTURE",
                    "minValue": 22.5,
                    "maxValue": 45,
                    "severity": "CRITICAL",
                }
            ]
        }
    )

    @model_validator(mode="after")
    def minimum_below_maximum(self) -> "AlertRuleRequest":
        if self.min_value >= self.max_value:
            raise ValueError("minValue must be below maxValue")
        return self


class AlertRuleResponse(ResponseModel):
    rule_id: str
    crop_type: str
    region: str
    metric: str
    unit: str
    min_value: float
    max_value: float
    severity: str
    version: int
    updated_at: datetime
