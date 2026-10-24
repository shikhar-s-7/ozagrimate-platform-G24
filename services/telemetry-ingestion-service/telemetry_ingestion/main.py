"""Telemetry Ingestion Service: the FastAPI app (port 8081).

Run from the repository root:
    python -m uvicorn telemetry_ingestion.main:app --app-dir services/telemetry-ingestion-service --port 8081
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from fastapi import FastAPI
from ozagrimate_common import register_error_handlers, utc_now

from .api.device_routes import router as device_router
from .api.telemetry_routes import router as telemetry_router
from .device_registry.repository import seeded_device_repository
from .device_registry.service import DeviceRegistryService
from .duplicate_filter.filter import DuplicateFilter
from .event_publisher.publisher import InMemoryEventPublisher
from .ingestion_pipeline.pipeline import IngestionPipeline
from .protocol_adapters.registry import default_adapter_registry
from .reading_store.repository import InMemoryReadingRepository
from .validator.rules import ReadingValidator


def create_app(clock: Callable[[], datetime] = utc_now) -> FastAPI:
    """Build the app and wire its components with fresh in-memory data."""
    app = FastAPI(
        title="OzAgriMate - Telemetry Ingestion Service",
        version="1.0.0",
        description="Endpoints #1-3: ingest sensor readings, read device health, replace device configuration.",
    )
    register_error_handlers(app)

    devices = DeviceRegistryService(seeded_device_repository(clock()), clock=clock)
    readings = InMemoryReadingRepository()
    events = InMemoryEventPublisher()
    pipeline = IngestionPipeline(
        adapters=default_adapter_registry(),
        devices=devices,
        validator=ReadingValidator(),
        duplicate_filter=DuplicateFilter(),
        reading_store=readings,
        publisher=events,
        clock=clock,
    )

    app.state.devices = devices
    app.state.readings = readings
    app.state.events = events
    app.state.pipeline = pipeline

    app.include_router(telemetry_router)
    app.include_router(device_router)
    return app


app = create_app()
