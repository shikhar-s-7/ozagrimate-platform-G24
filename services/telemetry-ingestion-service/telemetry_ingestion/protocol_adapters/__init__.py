"""Protocol Adapters component.

One adapter per gateway protocol (HTTPS JSON, MQTT). Each turns its own message
format into the same canonical batch, so the rest of the service never sees
protocol differences (Adapter pattern; ADR-03, ASR18, C3).
"""

from .base import CanonicalBatch, CanonicalReading, MalformedPayload, ProtocolAdapter
from .https_json import HttpsJsonAdapter
from .mqtt import MqttAdapter, MqttMessage
from .registry import AdapterRegistry, UnsupportedProtocol, default_adapter_registry

__all__ = [
    "AdapterRegistry",
    "CanonicalBatch",
    "CanonicalReading",
    "HttpsJsonAdapter",
    "MalformedPayload",
    "MqttAdapter",
    "MqttMessage",
    "ProtocolAdapter",
    "UnsupportedProtocol",
    "default_adapter_registry",
]
