"""Endpoint tests for the Farm & Access Service (#7-8), success and error cases."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from farm_access.main import create_app

NOW = datetime(2026, 10, 22, 8, 45, tzinfo=timezone.utc)
ERROR_KEYS = {"timestamp", "status", "error", "message", "path"}
GRANTS_URL = "/api/v1/farms/FARM-001/access-grants"
OWNER = {"X-User-Id": "FARMER-001"}
NEW_GRANT = {"agronomistId": "AGR-001", "scopes": ["READ_TELEMETRY", "READ_ALERTS"], "expiresAt": "2027-06-30T00:00:00Z"}


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


def assert_error(response, status: int, message_part: str) -> None:
    assert response.status_code == status
    body = response.json()
    assert set(body) == ERROR_KEYS
    assert body["status"] == status
    assert message_part in body["message"]


# ---------- #7 POST /api/v1/farms/{farmId}/access-grants ----------

def test_owner_grants_an_agronomist_access(client: TestClient):
    response = client.post(GRANTS_URL, json=NEW_GRANT, headers=OWNER)

    assert response.status_code == 201
    assert response.headers["Location"] == "/api/v1/farms/FARM-001/access-grants/GRANT-002"
    assert response.json() == {
        "grantId": "GRANT-002",
        "farmId": "FARM-001",
        "agronomistId": "AGR-001",
        "agronomistName": "Mallee Agronomy Services",
        "scopes": ["READ_TELEMETRY", "READ_ALERTS"],
        "status": "ACTIVE",
        "grantedBy": "FARMER-001",
        "grantedAt": "2026-10-22T08:45:00Z",
        "expiresAt": "2027-06-30T00:00:00Z",
    }


def test_granting_access_publishes_an_access_granted_event(client: TestClient):
    client.post(GRANTS_URL, json=NEW_GRANT, headers=OWNER)

    [event] = client.app.state.events.published
    assert (event.topic, event.key, event.payload["eventType"]) == ("access.grants", "FARM-001", "AccessGranted")


def test_grant_without_expiry_and_with_local_time_expiry(client: TestClient):
    no_expiry = client.post(GRANTS_URL, json={"agronomistId": "AGR-001", "scopes": ["READ_REPORTS"]}, headers=OWNER)
    assert (no_expiry.status_code, no_expiry.json()["expiresAt"]) == (201, None)

    client.delete(GRANTS_URL + "/GRANT-002", headers=OWNER)
    local_time = client.post(GRANTS_URL, json={**NEW_GRANT, "expiresAt": "2027-06-30T10:00:00+10:00"}, headers=OWNER)
    assert local_time.json()["expiresAt"] == "2027-06-30T00:00:00Z"


def test_second_active_grant_for_the_same_agronomist_answers_409(client: TestClient):
    response = client.post(GRANTS_URL, json={**NEW_GRANT, "agronomistId": "AGR-002"}, headers=OWNER)

    assert_error(response, 409, "Agronomist AGR-002 already has an active grant (GRANT-001) on farm FARM-001")


def test_an_expired_grant_does_not_block_a_new_one(client: TestClient, clock: FakeClock):
    client.post(GRANTS_URL, json={**NEW_GRANT, "expiresAt": "2026-10-23T00:00:00Z"}, headers=OWNER)
    clock.advance(days=2)

    response = client.post(GRANTS_URL, json={**NEW_GRANT, "expiresAt": "2027-06-30T00:00:00Z"}, headers=OWNER)

    assert (response.status_code, response.json()["grantId"]) == (201, "GRANT-003")


def test_unknown_agronomist_answers_404(client: TestClient):
    response = client.post(GRANTS_URL, json={**NEW_GRANT, "agronomistId": "AGR-999"}, headers=OWNER)

    assert_error(response, 404, "Agronomist AGR-999 is not registered")


def test_unknown_farm_answers_404(client: TestClient):
    response = client.post("/api/v1/farms/FARM-999/access-grants", json=NEW_GRANT, headers=OWNER)

    assert_error(response, 404, "Farm FARM-999 does not exist")


def test_someone_other_than_the_owner_answers_403(client: TestClient):
    response = client.post(GRANTS_URL, json=NEW_GRANT, headers={"X-User-Id": "FARMER-002"})

    assert_error(response, 403, "User FARMER-002 does not own farm FARM-001")
    assert client.app.state.events.published == []


def test_missing_user_header_answers_401(client: TestClient):
    response = client.post(GRANTS_URL, json=NEW_GRANT)

    assert_error(response, 401, "Missing X-User-Id header")
    assert response.headers["WWW-Authenticate"].startswith("Bearer")


@pytest.mark.parametrize(
    ("body", "message_part"),
    [
        ({**NEW_GRANT, "expiresAt": "2026-10-01T00:00:00Z"}, "expiresAt must be in the future"),
        ({**NEW_GRANT, "scopes": []}, "scopes: List should have at least 1 item"),
        ({**NEW_GRANT, "scopes": ["READ_ALERTS", "READ_ALERTS"]}, "scopes: must not repeat a scope"),
        ({**NEW_GRANT, "scopes": ["WRITE_EVERYTHING"]}, "scopes.0: Input should be"),
        ({"scopes": ["READ_ALERTS"]}, "agronomistId: Field required"),
        ({**NEW_GRANT, "role": "ADMIN"}, "role: Extra inputs are not permitted"),
    ],
)
def test_invalid_grant_requests_answer_400(client: TestClient, body: dict, message_part: str):
    assert_error(client.post(GRANTS_URL, json=body, headers=OWNER), 400, message_part)


# ---------- #8 DELETE /api/v1/farms/{farmId}/access-grants/{grantId} ----------

def test_owner_revokes_a_grant(client: TestClient):
    response = client.delete(GRANTS_URL + "/GRANT-001", headers=OWNER)

    assert response.status_code == 204
    assert response.content == b""
    [event] = client.app.state.events.published
    assert (event.payload["eventType"], event.payload["grantId"], event.payload["revokedBy"]) == (
        "AccessRevoked",
        "GRANT-001",
        "FARMER-001",
    )


def test_revoking_the_same_grant_twice_answers_404(client: TestClient):
    client.delete(GRANTS_URL + "/GRANT-001", headers=OWNER)

    assert_error(client.delete(GRANTS_URL + "/GRANT-001", headers=OWNER), 404, "No active grant GRANT-001 on farm FARM-001")


def test_a_revoked_agronomist_can_be_granted_access_again(client: TestClient):
    client.delete(GRANTS_URL + "/GRANT-001", headers=OWNER)

    response = client.post(GRANTS_URL, json={**NEW_GRANT, "agronomistId": "AGR-002"}, headers=OWNER)

    assert response.status_code == 201


def test_revoking_an_unknown_grant_or_another_farms_grant_answers_404(client: TestClient):
    assert_error(client.delete(GRANTS_URL + "/GRANT-999", headers=OWNER), 404, "No active grant GRANT-999")
    other_farm = client.delete("/api/v1/farms/FARM-002/access-grants/GRANT-001", headers={"X-User-Id": "FARMER-002"})
    assert_error(other_farm, 404, "No active grant GRANT-001 on farm FARM-002")


def test_revoke_checks_the_caller_and_the_owner(client: TestClient):
    assert_error(client.delete(GRANTS_URL + "/GRANT-001"), 401, "Missing X-User-Id header")
    assert_error(client.delete(GRANTS_URL + "/GRANT-001", headers={"X-User-Id": "FARMER-002"}), 403, "does not own farm FARM-001")
    assert_error(client.delete("/api/v1/farms/FARM-999/access-grants/GRANT-001", headers=OWNER), 404, "Farm FARM-999 does not exist")
