"""Runs a gateway batch through adapters, checks, storage and event publishing."""

from __future__ import annotations

import itertools
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ozagrimate_common import ApiError

from ..device_registry.service import DeviceRegistryService
from ..duplicate_filter.filter import DuplicateFilter
from ..event_publisher.publisher import InMemoryEventPublisher
from ..protocol_adapters.base import CanonicalReading, MalformedPayload
from ..protocol_adapters.registry import AdapterRegistry
from ..reading_store.repository import InMemoryReadingRepository, StoredReading
from ..validator.rules import ReadingRejected, ReadingValidator, RejectionReason


@dataclass(frozen=True)
class RejectionRecord:
    index: int
    device_id: str
    sequence_no: int
    reason: str
    message: str


@dataclass(frozen=True)
class IngestionResult:
    """The acknowledgement returned to the gateway (ASR27)."""

    batch_id: str
    gateway_id: str
    farm_id: str
    received_at: datetime
    received: int
    accepted: int
    duplicates: int
    rejected: int
    rejections: list[RejectionRecord]


class IngestionPipeline:
    def __init__(
        self,
        *,
        adapters: AdapterRegistry,
        devices: DeviceRegistryService,
        validator: ReadingValidator,
        duplicate_filter: DuplicateFilter,
        reading_store: InMemoryReadingRepository,
        publisher: InMemoryEventPublisher,
        clock: Callable[[], datetime],
    ) -> None:
        self._adapters = adapters
        self._devices = devices
        self._validator = validator
        self._duplicates = duplicate_filter
        self._store = reading_store
        self._publisher = publisher
        self._clock = clock
        self._batch_numbers = itertools.count(1)

    def ingest(self, protocol: str, payload: Any) -> IngestionResult:
        received_at = self._clock()
        try:
            batch = self._adapters.get(protocol).to_canonical(payload)
        except MalformedPayload as exc:
            raise ApiError(400, str(exc)) from exc

        gateway = self._devices.find_gateway(batch.gateway_id)
        if gateway is None:
            raise ApiError(400, f"Gateway {batch.gateway_id} is not registered")

        batch_id = f"BATCH-{next(self._batch_numbers):04d}"
        accepted: list[CanonicalReading] = []
        rejections: list[RejectionRecord] = []
        duplicates = 0
        newest_sequence: dict[str, int] = {}

        for index, reading in enumerate(batch.readings):
            device = self._devices.find_device(reading.device_id)
            if device is None or device.gateway_id != gateway.gateway_id:
                rejections.append(
                    RejectionRecord(
                        index,
                        reading.device_id,
                        reading.sequence_no,
                        RejectionReason.UNKNOWN_DEVICE.value,
                        f"Device {reading.device_id} is not registered to gateway {gateway.gateway_id}",
                    )
                )
                continue

            newest_sequence[device.device_id] = max(newest_sequence.get(device.device_id, -1), reading.sequence_no)

            if self._duplicates.is_duplicate(device.device_id, reading.sequence_no):
                duplicates += 1
                continue

            try:
                normalised = self._validator.normalise(reading, device.device_type, received_at)
            except ReadingRejected as rejection:
                rejections.append(
                    RejectionRecord(index, reading.device_id, reading.sequence_no, rejection.reason.value, rejection.message)
                )
                continue

            self._store.save(
                StoredReading(
                    batch_id=batch_id,
                    farm_id=gateway.farm_id,
                    gateway_id=gateway.gateway_id,
                    device_id=normalised.device_id,
                    sequence_no=normalised.sequence_no,
                    metric=normalised.metric,
                    value=normalised.value,
                    unit=normalised.unit,
                    captured_at=normalised.captured_at,
                    received_at=received_at,
                )
            )
            self._duplicates.remember(normalised.device_id, normalised.sequence_no)
            accepted.append(normalised)

        for device_id, sequence_no in newest_sequence.items():
            self._devices.record_contact(device_id, sequence_no, received_at)

        if accepted:
            self._publisher.publish_telemetry_received(
                batch_id=batch_id,
                farm_id=gateway.farm_id,
                gateway_id=gateway.gateway_id,
                received_at=received_at,
                readings=accepted,
            )

        return IngestionResult(
            batch_id=batch_id,
            gateway_id=gateway.gateway_id,
            farm_id=gateway.farm_id,
            received_at=received_at,
            received=len(batch.readings),
            accepted=len(accepted),
            duplicates=duplicates,
            rejected=len(rejections),
            rejections=rejections,
        )
