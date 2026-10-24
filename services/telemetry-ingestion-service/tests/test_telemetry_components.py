"""Unit tests for components that the endpoints do not fully exercise."""

import json
from datetime import datetime, timezone

import pytest

from telemetry_ingestion.main import create_app
from telemetry_ingestion.protocol_adapters import (
    AdapterRegistry,
    CanonicalReading,
    MalformedPayload,
    MqttAdapter,
    MqttMessage,
    UnsupportedProtocol,
    default_adapter_registry,
)
from telemetry_ingestion.validator import ReadingRejected, ReadingValidator, RejectionReason

NOW = datetime(2026, 10, 22, 8, 45, tzinfo=timezone.utc)
EPOCH_0840 = int(datetime(2026, 10, 22, 8, 40, tzinfo=timezone.utc).timestamp())


def mqtt_message(rows: list, topic: str = "farms/FARM-001/gateways/GW-01/telemetry") -> MqttMessage:
    return MqttMessage(topic=topic, payload=json.dumps({"r": rows}).encode())


def canonical(metric: str, value: float, unit: str) -> CanonicalReading:
    return CanonicalReading("DEV-1", 1, metric, value, unit, NOW)


# ---------- Protocol Adapters ----------

def test_mqtt_adapter_turns_compact_rows_into_a_canonical_batch():
    batch = MqttAdapter().to_canonical(mqtt_message([["DEV-1001", 200, "SOIL_MOISTURE", 0.31, "fraction", EPOCH_0840]]))

    assert batch.gateway_id == "GW-01"
    assert batch.protocol == "mqtt"
    assert batch.readings == (
        CanonicalReading("DEV-1001", 200, "SOIL_MOISTURE", 0.31, "fraction", datetime(2026, 10, 22, 8, 40, tzinfo=timezone.utc)),
    )


@pytest.mark.parametrize(
    "message",
    [
        mqtt_message([], topic="farms/FARM-001/telemetry"),
        MqttMessage("farms/FARM-001/gateways/GW-01/telemetry", b"not json"),
        mqtt_message([["DEV-1001", 200, "SOIL_MOISTURE"]]),
        mqtt_message([]),
    ],
)
def test_mqtt_adapter_rejects_malformed_messages(message: MqttMessage):
    with pytest.raises(MalformedPayload):
        MqttAdapter().to_canonical(message)


def test_registry_refuses_a_protocol_without_an_adapter():
    with pytest.raises(UnsupportedProtocol):
        AdapterRegistry([]).get("coap")
    assert default_adapter_registry().protocols == ["https-json", "mqtt"]


def test_mqtt_and_https_batches_share_one_pipeline():
    app = create_app(clock=lambda: NOW)

    result = app.state.pipeline.ingest("mqtt", mqtt_message([["DEV-1001", 200, "SOIL_MOISTURE", 0.31, "fraction", EPOCH_0840]]))

    assert (result.farm_id, result.accepted, result.rejected) == ("FARM-001", 1, 0)
    assert app.state.readings.for_device("DEV-1001")[0].value == 31.0


# ---------- Validator ----------

@pytest.mark.parametrize(
    ("metric", "value", "unit", "expected"),
    [
        ("SOIL_MOISTURE", 0.274, "fraction", (27.4, "%")),
        ("SOIL_TEMPERATURE", 68, "F", (20.0, "C")),
        ("AIR_TEMPERATURE", -4, "F", (-20.0, "C")),
        ("RAINFALL", 0.5, "in", (12.7, "mm")),
        ("WATER_FLOW", 10, "gal/min", (37.85, "L/min")),
    ],
)
def test_validator_converts_to_canonical_units(metric: str, value: float, unit: str, expected: tuple):
    device_type = {
        "SOIL_MOISTURE": "SOIL_MOISTURE_PROBE",
        "SOIL_TEMPERATURE": "SOIL_MOISTURE_PROBE",
        "AIR_TEMPERATURE": "WEATHER_STATION",
        "RAINFALL": "WEATHER_STATION",
        "WATER_FLOW": "WATER_FLOW_METER",
    }[metric]

    result = ReadingValidator().normalise(canonical(metric, value, unit), device_type, NOW)

    assert (result.value, result.unit) == expected


def test_validator_rejects_values_that_are_not_numbers_in_range():
    with pytest.raises(ReadingRejected) as rejected:
        ReadingValidator().normalise(canonical("SOIL_MOISTURE", float("nan"), "%"), "SOIL_MOISTURE_PROBE", NOW)

    assert rejected.value.reason is RejectionReason.OUT_OF_RANGE
