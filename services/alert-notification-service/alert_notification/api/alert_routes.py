"""Endpoint #4: list a farm's alerts, optionally filtered by status."""

from fastapi import APIRouter, Depends, Header, Path, Query
from ozagrimate_common import ErrorBody

from ..alert_manager.models import AlertStatus
from ..alert_manager.service import AlertManager
from .dependencies import get_alert_manager
from .schemas import AlertResponse, FarmAlertsResponse

router = APIRouter(prefix="/api/v1/farms", tags=["Alert API"])


@router.get(
    "/{farmId}/alerts",
    response_model=FarmAlertsResponse,
    summary="List a farm's alerts, newest first, optionally filtered by status",
    responses={
        400: {"model": ErrorBody, "description": "Unknown status value"},
        401: {"model": ErrorBody, "description": "No X-User-Id header"},
        403: {"model": ErrorBody, "description": "Caller is not the owner and has no READ_ALERTS grant"},
        404: {"model": ErrorBody, "description": "Unknown farm"},
    },
)
def list_farm_alerts(
    farm_id: str = Path(alias="farmId", examples=["FARM-001"]),
    status: AlertStatus | None = Query(default=None, description="OPEN, ACKNOWLEDGED or RESOLVED; omit for all."),
    user_id: str | None = Header(
        default=None,
        alias="X-User-Id",
        description="Set by the API Gateway after it validates the caller's token (ADR-05).",
        examples=["FARMER-001"],
    ),
    alerts: AlertManager = Depends(get_alert_manager),
) -> FarmAlertsResponse:
    """The farm's owner, or an agronomist the owner has granted READ_ALERTS, may
    read its alerts (ASR7, ASR9). Each alert shows how it was delivered (ADR-04)."""
    found = alerts.list_for_farm(caller_id=user_id, farm_id=farm_id, status=status)
    return FarmAlertsResponse(
        farm_id=farm_id,
        status=status,
        count=len(found),
        alerts=[
            AlertResponse(
                alert_id=alert.alert_id,
                rule_id=alert.rule_id,
                device_id=alert.device_id,
                metric=alert.metric,
                value=alert.value,
                unit=alert.unit,
                min_value=alert.min_value,
                max_value=alert.max_value,
                breach=alert.breach,
                severity=alert.severity,
                status=alert.status,
                message=alert.message,
                raised_at=alert.raised_at,
                delivery_status=delivery.status,
                delivery_attempts=delivery.attempts,
            )
            for alert, delivery in found
        ],
    )
