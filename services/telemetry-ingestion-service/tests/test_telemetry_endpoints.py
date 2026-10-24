"""Endpoint tests for the Telemetry Ingestion Service (#1-3), success and error cases."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from telemetry_ingestion.main import create_app

NOW = datetime(2026, 10, 22, 8, 45, tzinfo=timezone.utc)
ERROR_KEYS = {"timestamp", "status", "error", "message", "path"}


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **delta: float) -> None:
        self.now += timedelta(**delta)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def client(clock: FakeClock) -> TestClient:
    return TestClient(create_app(clock=clock))


def reading(device_id: str, sequence_no: int, metric: str, value: float, unit: str, captured_at: str = "2026-10-22T08:40:00Z") -> dict:
    return {
        "deviceId": device_id,
        "sequenceNo": sequence_no,
        "metric": metric,
        "value": value,
        "unit": unit,
        "capturedAt": captured_at,
    }


VALID_BATCH = {
    "gatewayId": "GW-01",
    "readings": [
        reading("DEV-1001", 101, "SOIL_MOISTURE", 0.274, "fraction"),
        reading("DEV-1002", 57, "AIR_TEMPERATURE", 75.2, "F"),
        reading("DEV-1002", 58, "RAINFALL", 1.2, "mm"),
    ],
}


def assert_error(response, status: int, message_part: str) -> None:
    assert response.status_code == status
    body = response.json()
    assert set(body) == ERROR_KEYS
    assert body["status"] == status
    assert message_part in body["message"]


# ---------- #1 POST /api/v1/telemetry/readings ----------

def test_ingest_accepts_a_valid_batch_and_acknowledges_it(client: TestClient):
    response = client.post("/api/v1/telemetry/readings", json=VALID_BATCH)

    assert response.status_code == 202
    assert response.json() == {
        "batchId": "BATCH-0001",
        "gatewayId": "GW-01",
        "farmId": "FARM-001",
        "receivedAt": "2026-10-22T08:45:00Z",
        "received": 3,
        "accepted": 3,
        "duplicates": 0,
        "rejected": 0,
        "rejections": [],
    }


def test_ingest_stores_readings_in_canonical_units_and_publishes_one_event(client: TestClient):
    client.post("/api/v1/telemetry/readings", json=VALID_BATCH)

    stored = {(r.device_id, r.metric): (r.value, r.unit) for r in client.app.state.readings.all()}
    assert stored == {
        ("DEV-1001", "SOIL_MOISTURE"): (27.4, "%"),
        ("DEV-1002", "AIR_TEMPERATURE"): (24.0, "C"),
        ("DEV-1002", "RAINFALL"): (1.2, "mm"),
    }
    [event] = client.app.state.events.published
    assert (event.topic, event.key) == ("telemetry.received", "FARM-001")
    assert event.payload["eventType"] == "TelemetryReceived"
    assert len(event.payload["readings"]) == 3


def test_resending_a_batch_counts_every_reading_as_a_duplicate(client: TestClient):
    client.post("/api/v1/telemetry/readings", json=VALID_BATCH)

    response = client.post("/api/v1/telemetry/readings", json=VALID_BATCH)

    assert response.status_code == 202
    body = response.json()
    assert (body["batchId"], body["accepted"], body["duplicates"], body["rejected"]) == ("BATCH-0002", 0, 3, 0)
    assert client.app.state.readings.count() == 3
    assert len(client.app.state.events.published) == 1  # nothing new to publish


def test_ingest_lists_each_rejected_reading_and_keeps_the_rest(client: TestClient):
    batch = {
        "gatewayId": "GW-01",
        "readings": [
            reading("DEV-1001", 101, "SOIL_MOISTURE", 31.5, "%"),
            reading("DEV-2001", 881, "WATER_FLOW", 12, "L/min"),
            reading("DEV-1001", 102, "RAINFALL", 1, "mm"),
            reading("DEV-1001", 103, "SOIL_MOISTURE", 20, "kPa"),
            reading("DEV-1001", 104, "SOIL_MOISTURE", 140, "%"),
            reading("DEV-1001", 105, "SOIL_MOISTURE", 30, "%", captured_at="2026-10-22T09:00:00Z"),
        ],
    }

    response = client.post("/api/v1/telemetry/readings", json=batch)

    assert response.status_code == 202
    body = response.json()
    assert (body["received"], body["accepted"], body["rejected"]) == (6, 1, 5)
    assert [(r["index"], r["reason"]) for r in body["rejections"]] == [
        (1, "UNKNOWN_DEVICE"),
        (2, "UNSUPPORTED_METRIC"),
        (3, "UNSUPPORTED_UNIT"),
        (4, "OUT_OF_RANGE"),
        (5, "FUTURE_TIMESTAMP"),
    ]
    assert body["rejections"][1]["message"] == "A SOIL_MOISTURE_PROBE does not report RAINFALL"


@pytest.mark.parametrize(
    ("batch", "message_part"),
    [
        ({"gatewayId": "GW-01", "readings": []}, "readings: List should have at least 1 item"),
        ({"readings": VALID_BATCH["readings"]}, "gatewayId: Field required"),
        ({"gatewayId": "GW-01", "readings": [reading("DEV-1001", -1, "SOIL_MOISTURE", 30, "%")]}, "readings.0.sequenceNo"),
        ({"gatewayId": "GW-01", "readings": [reading("DEV-1001", 1, "LEAF_WETNESS", 3, "%")]}, "readings.0.metric"),
        ({"gatewayId": "GW-01", "readings": [reading("DEV-1001", 1, "SOIL_MOISTURE", 30, "%", "2026-10-22T08:40:00")]}, "readings.0.capturedAt"),
        ({**VALID_BATCH, "firmware": "2.1"}, "firmware: Extra inputs are not permitted"),
    ],
)
def test_malformed_batches_answer_400(client: TestClient, batch: dict, message_part: str):
    response = client.post("/api/v1/telemetry/readings", json=batch)

    assert_error(response, 400, message_part)
    assert client.app.state.readings.count() == 0


def test_body_that_is_not_json_answers_400(client: TestClient):
    response = client.post(
        "/api/v1/telemetry/readings", content=b"{not json", headers={"Content-Type": "application/json"}
    )

    assert_error(response, 400, "Request body is not valid JSON")


def test_unregistered_gateway_answers_400(client: TestClient):
    response = client.post("/api/v1/telemetry/readings", json={**VALID_BATCH, "gatewayId": "GW-99"})

    assert_error(response, 400, "Gateway GW-99 is not registered")


# ---------- #2 GET /api/v1/devices/{deviceId}/health ----------

def test_health_reports_a_recently_seen_device_as_online(client: TestClient):
    response = client.get("/api/v1/devices/DEV-1001/health")

    assert response.status_code == 200
    assert response.json() == {
        "deviceId": "DEV-1001",
        "farmId": "FARM-001",
        "gatewayId": "GW-01",
        "deviceType": "SOIL_MOISTURE_PROBE",
        "status": "ONLINE",
        "lastSeenAt": "2026-10-22T08:40:00Z",
        "minutesSinceLastSeen": 5,
        "offlineAfterMinutes": 30,
        "lastSequenceNo": 100,
        "configurationVersion": 1,
    }


def test_health_reports_a_device_silent_for_two_hours_as_offline(client: TestClient):
    body = client.get("/api/v1/devices/DEV-2001/health").json()

    assert (body["status"], body["minutesSinceLastSeen"]) == ("OFFLINE", 120)


def test_device_goes_offline_after_30_minutes_of_silence(client: TestClient, clock: FakeClock):
    clock.advance(minutes=25)  # silent for exactly 30 minutes
    assert client.get("/api/v1/devices/DEV-1001/health").json()["status"] == "ONLINE"

    clock.advance(minutes=1)
    assert client.get("/api/v1/devices/DEV-1001/health").json()["status"] == "OFFLINE"


def test_ingesting_a_reading_records_contact_with_the_device(client: TestClient, clock: FakeClock):
    clock.advance(hours=3)
    batch = {"gatewayId": "GW-02", "readings": [reading("DEV-2001", 881, "WATER_FLOW", 12.5, "L/min", "2026-10-22T11:44:00Z")]}

    client.post("/api/v1/telemetry/readings", json=batch)
    body = client.get("/api/v1/devices/DEV-2001/health").json()

    assert (body["status"], body["lastSeenAt"], body["lastSequenceNo"]) == ("ONLINE", "2026-10-22T11:45:00Z", 881)


def test_health_of_an_unknown_device_answers_404(client: TestClient):
    assert_error(client.get("/api/v1/devices/DEV-9999/health"), 404, "Device DEV-9999 is not registered")


# ---------- #3 PUT /api/v1/devices/{deviceId}/configuration ----------

NEW_CONFIGURATION = {"samplingIntervalSeconds": 300, "reportingIntervalSeconds": 900, "bufferWhenOffline": True}


def test_configuration_update_stores_a_new_version_pending_device_sync(client: TestClient):
    response = client.put("/api/v1/devices/DEV-1001/configuration", json=NEW_CONFIGURATION)

    assert response.status_code == 200
    assert response.json() == {
        "deviceId": "DEV-1001",
        "samplingIntervalSeconds": 300,
        "reportingIntervalSeconds": 900,
        "bufferWhenOffline": True,
        "version": 2,
        "syncStatus": "PENDING_DEVICE_SYNC",
        "updatedAt": "2026-10-22T08:45:00Z",
    }
    assert client.get("/api/v1/devices/DEV-1001/health").json()["configurationVersion"] == 2


def test_repeating_the_same_configuration_changes_nothing(client: TestClient):
    first = client.put("/api/v1/devices/DEV-1001/configuration", json=NEW_CONFIGURATION).json()
    second = client.put("/api/v1/devices/DEV-1001/configuration", json=NEW_CONFIGURATION).json()

    assert second == first


@pytest.mark.parametrize(
    ("configuration", "message_part"),
    [
        ({**NEW_CONFIGURATION, "samplingIntervalSeconds": 30}, "samplingIntervalSeconds: Input should be greater than or equal to 60"),
        ({**NEW_CONFIGURATION, "reportingIntervalSeconds": 100_000}, "reportingIntervalSeconds: Input should be less than or equal to 86400"),
        ({**NEW_CONFIGURATION, "samplingIntervalSeconds": 900, "reportingIntervalSeconds": 300}, "reportingIntervalSeconds must be greater than or equal to samplingIntervalSeconds"),
        ({"samplingIntervalSeconds": 300, "reportingIntervalSeconds": 900}, "bufferWhenOffline: Field required"),
    ],
)
def test_invalid_configuration_answers_400(client: TestClient, configuration: dict, message_part: str):
    response = client.put("/api/v1/devices/DEV-1001/configuration", json=configuration)

    assert_error(response, 400, message_part)
    assert client.get("/api/v1/devices/DEV-1001/health").json()["configurationVersion"] == 1


def test_configuration_of_an_unknown_device_answers_404(client: TestClient):
    response = client.put("/api/v1/devices/DEV-9999/configuration", json=NEW_CONFIGURATION)

    assert_error(response, 404, "Device DEV-9999 is not registered")


# ---------- the shared error body ----------

def test_unknown_routes_and_methods_use_the_agreed_error_body(client: TestClient):
    assert_error(client.get("/api/v1/sensors"), 404, "No endpoint matches GET /api/v1/sensors")
    assert_error(client.delete("/api/v1/devices/DEV-1001/health"), 405, "DELETE is not allowed")
