"""Remembers the (deviceId, sequenceNo) key of every accepted reading."""

from __future__ import annotations


class DuplicateFilter:
    """In-memory stand-in for the unique (device_id, sequence_no) key in the Telemetry Store.

    In production the key would live in the store itself (or a cache with a
    replay-window expiry), so every ingestion instance shares it.
    """

    def __init__(self) -> None:
        self._seen: set[tuple[str, int]] = set()

    def is_duplicate(self, device_id: str, sequence_no: int) -> bool:
        return (device_id, sequence_no) in self._seen

    def remember(self, device_id: str, sequence_no: int) -> None:
        self._seen.add((device_id, sequence_no))
