"""Finds the adapter for a protocol, so new protocols plug in without pipeline changes."""

from __future__ import annotations

from collections.abc import Iterable

from .base import ProtocolAdapter
from .https_json import HttpsJsonAdapter
from .mqtt import MqttAdapter


class UnsupportedProtocol(LookupError):
    """No adapter is registered for the protocol."""


class AdapterRegistry:
    def __init__(self, adapters: Iterable[ProtocolAdapter]) -> None:
        self._adapters = {adapter.protocol: adapter for adapter in adapters}

    def get(self, protocol: str) -> ProtocolAdapter:
        try:
            return self._adapters[protocol]
        except KeyError:
            raise UnsupportedProtocol(f"No adapter is registered for protocol '{protocol}'") from None

    @property
    def protocols(self) -> list[str]:
        return sorted(self._adapters)


def default_adapter_registry() -> AdapterRegistry:
    """The adapters the service ships with (ADR-03)."""
    return AdapterRegistry([HttpsJsonAdapter(), MqttAdapter()])
