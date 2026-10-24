"""Checks the service skeleton starts and uses the agreed error body.

Add the tests for endpoints #4-6 alongside this file.
"""

from fastapi.testclient import TestClient

from alert_notification.main import create_app


def test_unknown_route_answers_with_the_agreed_error_body():
    client = TestClient(create_app())

    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert set(response.json()) == {"timestamp", "status", "error", "message", "path"}
