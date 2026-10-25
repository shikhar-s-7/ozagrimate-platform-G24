"""Component tests: threshold evaluation, push-then-SMS delivery and the access cache."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from alert_notification.main import create_app

NOW = datetime(2026, 10, 22, 8, 45, tzinfo=timezone.utc)


def telemetry(farm_id: str, value: float, metric: str = "SOIL_MOISTURE", device_id: str = "DEV-1003") -> dict:
    return {
        "eventType": "TelemetryReceived",
        "schemaVersion": 1,
        "farmId": farm_id,
        "gatewayId": "GW-01",
        "receivedAt": "2026-10-22T08:45:00Z",
        "readings": [{"deviceId": device_id, "sequenceNo": 1, "metric": metric, "value": value, "unit": "%"}],
    }


def make_app():
    return TestClient(create_app(clock=lambda: NOW)).app


def test_a_reading_inside_the_band_raises_nothing():
    app = make_app()

    assert app.state.evaluator.on_telemetry_received(telemetry("FARM-001", 30.0)) == []


def test_a_breach_raises_an_alert_publishes_it_and_pushes_it():
    app = make_app()

    [alert] = app.state.evaluator.on_telemetry_received(telemetry("FARM-001", 12.0))

    assert (alert.alert_id, alert.breach, alert.severity) == ("ALERT-005", "BELOW_MIN", "CRITICAL")
    event = app.state.events.published[-1]
    assert (event.topic, event.key, event.payload["eventType"]) == ("alerts.raised", "FARM-001", "AlertRaised")
    assert app.state.push.sent[-1][0] == "FARMER-001"
    assert app.state.tracker.summary(alert.alert_id).status == "PUSH_DELIVERED"


def test_a_repeat_breach_while_the_alert_is_open_is_not_raised_again():
    app = make_app()
    app.state.evaluator.on_telemetry_received(telemetry("FARM-001", 12.0))

    assert app.state.evaluator.on_telemetry_received(telemetry("FARM-001", 11.0)) == []


def test_readings_from_an_unknown_farm_are_ignored():
    app = make_app()

    assert app.state.evaluator.on_telemetry_received(telemetry("FARM-999", 1.0)) == []


def test_an_unconfirmed_push_falls_back_to_sms_after_two_minutes():
    app = make_app()
    app.state.push.unreachable_users = {"FARMER-001"}
    [alert] = app.state.evaluator.on_telemetry_received(telemetry("FARM-001", 12.0))

    assert app.state.dispatcher.fall_back_to_sms(NOW + timedelta(seconds=119)) == []
    assert app.state.dispatcher.fall_back_to_sms(NOW + timedelta(minutes=2)) == [alert.alert_id]
    assert app.state.sms.sent[-1] == ("+61400000001", alert.message)
    assert app.state.tracker.summary(alert.alert_id).status == "SMS_DELIVERED"
    assert app.state.dispatcher.fall_back_to_sms(NOW + timedelta(minutes=3)) == []


def test_sms_is_retried_when_the_provider_fails():
    app = make_app()
    app.state.push.unreachable_users = {"FARMER-001"}
    app.state.sms.failures_left = 2
    [alert] = app.state.evaluator.on_telemetry_received(telemetry("FARM-001", 12.0))

    app.state.dispatcher.fall_back_to_sms(NOW + timedelta(minutes=2))

    statuses = [(a.channel, a.status) for a in app.state.tracker.attempts(alert.alert_id)]
    assert statuses == [("PUSH", "SENT"), ("SMS", "FAILED"), ("SMS", "FAILED"), ("SMS", "DELIVERED")]


def test_access_events_from_farm_and_access_change_who_can_read_alerts():
    client = TestClient(create_app(clock=lambda: NOW))
    cache = client.app.state.farms
    url, agronomist = "/api/v1/farms/FARM-001/alerts", {"X-User-Id": "AGR-001"}
    assert client.get(url, headers=agronomist).status_code == 403

    cache.apply_access_event(
        {"eventType": "AccessGranted", "grantId": "GRANT-002", "farmId": "FARM-001", "agronomistId": "AGR-001",
         "scopes": ["READ_ALERTS"], "expiresAt": "2027-06-30T00:00:00Z"}
    )
    assert client.get(url, headers=agronomist).status_code == 200

    cache.apply_access_event({"eventType": "AccessRevoked", "grantId": "GRANT-002", "farmId": "FARM-001"})
    assert client.get(url, headers=agronomist).status_code == 403


def test_a_grant_without_read_alerts_or_past_expiry_gives_no_access():
    client = TestClient(create_app(clock=lambda: NOW))
    cache = client.app.state.farms
    cache.apply_access_event(
        {"eventType": "AccessGranted", "grantId": "GRANT-002", "farmId": "FARM-001", "agronomistId": "AGR-001",
         "scopes": ["READ_TELEMETRY"], "expiresAt": None}
    )
    cache.apply_access_event(
        {"eventType": "AccessGranted", "grantId": "GRANT-003", "farmId": "FARM-002", "agronomistId": "AGR-001",
         "scopes": ["READ_ALERTS"], "expiresAt": "2026-10-01T00:00:00Z"}
    )

    assert client.get("/api/v1/farms/FARM-001/alerts", headers={"X-User-Id": "AGR-001"}).status_code == 403
    assert client.get("/api/v1/farms/FARM-002/alerts", headers={"X-User-Id": "AGR-001"}).status_code == 403
