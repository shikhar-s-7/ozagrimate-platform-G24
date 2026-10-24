"""Gives the routers the components that main.create_app() wired together."""

from fastapi import Request

from ..device_registry.service import DeviceRegistryService
from ..ingestion_pipeline.pipeline import IngestionPipeline


def get_pipeline(request: Request) -> IngestionPipeline:
    return request.app.state.pipeline


def get_devices(request: Request) -> DeviceRegistryService:
    return request.app.state.devices
