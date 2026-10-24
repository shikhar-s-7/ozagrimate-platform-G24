"""Endpoint #1: POST /api/v1/telemetry/readings."""

from fastapi import APIRouter, Depends, status
from ozagrimate_common import ErrorBody

from ..ingestion_pipeline.pipeline import IngestionPipeline
from .dependencies import get_pipeline
from .schemas import IngestionAck, ReadingBatchRequest

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry API"])


@router.post(
    "/readings",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=IngestionAck,
    summary="Ingest a batch of sensor readings from a farm gateway",
    responses={400: {"model": ErrorBody, "description": "Malformed batch or unregistered gateway"}},
)
def ingest_readings(
    batch: ReadingBatchRequest,
    pipeline: IngestionPipeline = Depends(get_pipeline),
) -> IngestionAck:
    """Accept a gateway's batch and acknowledge what happened to each reading (ASR27).

    Readings already accepted (same deviceId and sequenceNo) are counted as
    duplicates and not stored again, so gateways can safely replay the readings
    they buffered while offline (ADR-03). Readings from unknown devices, with an
    unsupported unit or out-of-range values are listed in ``rejections``.
    """
    result = pipeline.ingest("https-json", batch.model_dump())
    return IngestionAck.model_validate(result, from_attributes=True)
