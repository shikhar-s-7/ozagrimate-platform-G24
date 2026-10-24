# Alert & Notification Service

**Container:** Alert & Notification Service · **Port:** 8082 · **Endpoints:** #4–6

Checks incoming readings against alert rules set per crop and region, raises alerts, and notifies farmers by push notification, falling back to SMS when the push is not delivered.

```bash
# from the repository root
python -m uvicorn alert_notification.main:app --app-dir services/alert-notification-service --port 8082
```

## Endpoints

| # | Method and URL | Success | Errors |
|---|---|---|---|
| 4 | `GET /api/v1/farms/{farmId}/alerts?status=OPEN` | 200 | 400 unknown status; 404 unknown farm |
| 5 | `PUT /api/v1/alert-rules/{ruleId}` | 200 | 400 minimum not below maximum; 404 unknown rule |
| 6 | `DELETE /api/v1/alert-rules/{ruleId}` | 204 | 404 unknown rule (so a second delete answers 404) |

## Components → packages

| Component | Package |
|---|---|
| Alert API | `alert_notification/api/` (`alert_routes.py` for #4, `alert_rule_routes.py` for #5–6) |
| Rule Manager | `alert_notification/rule_manager/` |
| Threshold Evaluator | `alert_notification/threshold_evaluator/` |
| Alert Manager | `alert_notification/alert_manager/` |
| Notification Dispatcher | `alert_notification/notification_dispatcher/` |
| Delivery Tracker | `alert_notification/delivery_tracker/` |

## Conventions shared with the other two services

- Build components in `create_app(clock=utc_now)` in `main.py` and keep them on `app.state`, so every test gets fresh seeded data. Routers reach them through a small `dependencies.py`, as in `telemetry_ingestion/api/dependencies.py`.
- Inside each component package, the router calls the component's service class, which calls an in-memory repository.
- Raise `ApiError(status, message)` from `ozagrimate_common` for 404 and business-rule errors. Pydantic validation failures become 400 automatically. Both use the agreed error body.
- Pydantic request models use `alias_generator=to_camel`, `populate_by_name=True` and `extra="forbid"`. Use `Path(alias="farmId")` / `Path(alias="ruleId")` so URLs keep camelCase names. See `telemetry_ingestion/api/schemas.py`.
- Seed farms `FARM-001` and `FARM-002` (the same IDs as the other services), and alert rules from `RULE-001`.
- Give test files names unique across the repository (for example `test_alert_endpoints.py`), because pytest runs all three services' tests together.
