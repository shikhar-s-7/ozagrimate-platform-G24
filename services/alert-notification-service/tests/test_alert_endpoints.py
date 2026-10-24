"""Endpoint tests for the Alert & Notification Service (#4-6), success and error cases."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from alert_notification.main import create_app

NOW = datetime(2026, 10, 22, 8, 45, tzinfo=timezone.utc)
ERROR_KEYS = {"timestamp", "status", "error", "message", "path"}
ALERTS_URL = "/api/v1/farms/FARM-001/alerts"
OWNER = {"X-User-Id": "FARMER-001"}
RULE_URL = "/api/v1/alert-rules/RULE-001"
NEW_RULE = {
    "cropType": "WHEAT",
    "region": "RIVERINA-NSW",
    "metric": "SOIL_MOISTURE",
    "minValue": 22.5,
    "maxValue": 45,
    "severity": "CRITICAL",
}


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


# ---------- #4 GET /api/v1/farms/{farmId}/alerts?status=OPEN ----------

def test_owner_lists_open_alerts_with_sms_fallback_delivery(client: TestClient):
    response = client.get(ALERTS_URL, params={"status": "OPEN"}, headers=OWNER)

    assert response.status_code == 200
    assert response.json() == {
        "farmId": "FARM-001",
        "status": "OPEN",
        "count": 1,
        "alerts": [
            {
                "alertId": "ALERT-003",
                "ruleId": "RULE-001",
                "deviceId": "DEV-1001",
                "metric": "SOIL_MOISTURE",
                "value": 14.2,
                "unit": "%",
                "minValue": 20.0,
                "maxValue": 45.0,
                "breach": "BELOW_MIN",
                "severity": "CRITICAL",
                "status": "OPEN",
                "message": "SOIL_MOISTURE 14.2 % on DEV-1001 is below the minimum of 20 % for WHEAT in RIVERINA-NSW",
                "raisedAt": "2026-10-22T07:55:00Z",
                "deliveryStatus": "SMS_DELIVERED",
                "deliveryAttempts": 2,
            }
        ],
    }


def test_without_a_status_every_alert_is_listed_newest_first(client: TestClient):
    body = client.get(ALERTS_URL, headers=OWNER).json()

    assert (body["status"], body["count"]) == (None, 3)
    assert [(a["alertId"], a["status"]) for a in body["alerts"]] == [
        ("ALERT-003", "OPEN"),
        ("ALERT-002", "ACKNOWLEDGED"),
        ("ALERT-001", "RESOLVED"),
    ]


@pytest.mark.parametrize(("status", "alert_ids"), [("ACKNOWLEDGED", ["ALERT-002"]), ("RESOLVED", ["ALERT-001"])])
def test_each_status_filter(client: TestClient, status: str, alert_ids: list[str]):
    body = client.get(ALERTS_URL, params={"status": status}, headers=OWNER).json()

    assert [a["alertId"] for a in body["alerts"]] == alert_ids


def test_agronomist_with_a_grant_sees_the_farms_alerts(client: TestClient):
    response = client.get(ALERTS_URL, params={"status": "OPEN"}, headers={"X-User-Id": "AGR-002"})

    assert (response.status_code, response.json()["count"]) == (200, 1)


def test_a_farm_with_no_alerts_of_that_status_answers_an_empty_list(client: TestClient):
    response = client.get("/api/v1/farms/FARM-002/alerts", params={"status": "RESOLVED"}, headers={"X-User-Id": "FARMER-002"})

    assert response.json() == {"farmId": "FARM-002", "status": "RESOLVED", "count": 0, "alerts": []}


def test_unknown_status_answers_400(client: TestClient):
    response = client.get(ALERTS_URL, params={"status": "CLOSED"}, headers=OWNER)

    assert_error(response, 400, "status: Input should be 'OPEN', 'ACKNOWLEDGED' or 'RESOLVED'")


def test_unknown_farm_answers_404(client: TestClient):
    assert_error(client.get("/api/v1/farms/FARM-999/alerts", headers=OWNER), 404, "Farm FARM-999 does not exist")


def test_agronomist_without_a_grant_answers_403(client: TestClient):
    response = client.get(ALERTS_URL, headers={"X-User-Id": "AGR-001"})

    assert_error(response, 403, "User AGR-001 has no access to the alerts of farm FARM-001")


def test_missing_user_header_answers_401(client: TestClient):
    response = client.get(ALERTS_URL)

    assert_error(response, 401, "Missing X-User-Id header")
    assert response.headers["WWW-Authenticate"].startswith("Bearer")


# ---------- #5 PUT /api/v1/alert-rules/{ruleId} ----------

def test_replace_a_rule(client: TestClient):
    response = client.put(RULE_URL, json=NEW_RULE)

    assert response.status_code == 200
    assert response.json() == {
        "ruleId": "RULE-001",
        "cropType": "WHEAT",
        "region": "RIVERINA-NSW",
        "metric": "SOIL_MOISTURE",
        "unit": "%",
        "minValue": 22.5,
        "maxValue": 45.0,
        "severity": "CRITICAL",
        "version": 2,
        "updatedAt": "2026-10-22T08:45:00Z",
    }


def test_put_is_idempotent(client: TestClient, clock: FakeClock):
    client.put(RULE_URL, json=NEW_RULE)
    clock.advance(minutes=5)

    again = client.put(RULE_URL, json=NEW_RULE).json()

    assert (again["version"], again["updatedAt"]) == (2, "2026-10-22T08:45:00Z")


def test_new_limits_apply_to_the_next_reading_without_redeploying(client: TestClient):
    client.put(RULE_URL, json={**NEW_RULE, "minValue": 30})
    event = {
        "eventType": "TelemetryReceived",
        "farmId": "FARM-001",
        "receivedAt": "2026-10-22T08:45:00Z",
        "readings": [{"deviceId": "DEV-1003", "metric": "SOIL_MOISTURE", "value": 28.0, "unit": "%"}],
    }

    [alert] = client.app.state.evaluator.on_telemetry_received(event)

    assert (alert.rule_id, alert.breach, alert.min_value) == ("RULE-001", "BELOW_MIN", 30.0)


@pytest.mark.parametrize(
    ("body", "message_part"),
    [
        ({**NEW_RULE, "minValue": 50}, "minValue must be below maxValue"),
        ({**NEW_RULE, "minValue": 45}, "minValue must be below maxValue"),
        ({**NEW_RULE, "metric": "HUMIDITY"}, "metric: Input should be"),
        ({**NEW_RULE, "severity": "LOW"}, "severity: Input should be 'WARNING' or 'CRITICAL'"),
        ({**NEW_RULE, "cropType": "wheat"}, "cropType: String should match pattern"),
        ({k: v for k, v in NEW_RULE.items() if k != "maxValue"}, "maxValue: Field required"),
        ({**NEW_RULE, "owner": "FARMER-001"}, "owner: Extra inputs are not permitted"),
    ],
)
def test_invalid_rules_answer_400(client: TestClient, body: dict, message_part: str):
    assert_error(client.put(RULE_URL, json=body), 400, message_part)


def test_replacing_an_unknown_rule_answers_404(client: TestClient):
    assert_error(client.put("/api/v1/alert-rules/RULE-999", json=NEW_RULE), 404, "Alert rule RULE-999 does not exist")


# ---------- #6 DELETE /api/v1/alert-rules/{ruleId} ----------

def test_delete_a_rule(client: TestClient):
    response = client.delete("/api/v1/alert-rules/RULE-005")

    assert response.status_code == 204
    assert response.content == b""


def test_deleting_the_same_rule_twice_answers_404(client: TestClient):
    client.delete("/api/v1/alert-rules/RULE-005")

    assert_error(client.delete("/api/v1/alert-rules/RULE-005"), 404, "Alert rule RULE-005 does not exist")


def test_a_deleted_rule_no_longer_raises_alerts_and_cannot_be_replaced(client: TestClient):
    client.delete(RULE_URL)
    event = {
        "eventType": "TelemetryReceived",
        "farmId": "FARM-001",
        "receivedAt": "2026-10-22T08:45:00Z",
        "readings": [{"deviceId": "DEV-1003", "metric": "SOIL_MOISTURE", "value": 5.0, "unit": "%"}],
    }

    assert client.app.state.evaluator.on_telemetry_received(event) == []
    assert_error(client.put(RULE_URL, json=NEW_RULE), 404, "Alert rule RULE-001 does not exist")
    assert client.get(ALERTS_URL, params={"status": "OPEN"}, headers=OWNER).json()["count"] == 1
