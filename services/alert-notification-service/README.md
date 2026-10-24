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
| 4 | `GET /api/v1/farms/{farmId}/alerts?status=OPEN` | 200 | 400 unknown status; 401 no `X-User-Id`; 403 caller is not the owner and has no `READ_ALERTS` grant; 404 unknown farm |
| 5 | `PUT /api/v1/alert-rules/{ruleId}` | 200 | 400 minimum not below maximum (or another invalid field); 404 unknown rule |
| 6 | `DELETE /api/v1/alert-rules/{ruleId}` | 204 | 404 unknown rule (so a second delete answers 404) |

`status` is optional on #4: without it every alert for the farm is listed, newest first.

## Components → packages

| Component | Package | Responsibility |
|---|---|---|
| Alert API | `alert_notification/api/` (`alert_routes.py` for #4, `alert_rule_routes.py` for #5–6) | REST endpoints and Pydantic schemas |
| Rule Manager | `alert_notification/rule_manager/` | Thresholds stored as data per crop, region and metric; replaced or deleted through the API (ADR-08, ASR14) |
| Threshold Evaluator | `alert_notification/threshold_evaluator/` | Consumes `TelemetryReceived`; every limit comes from a rule, none is written in code |
| Alert Manager | `alert_notification/alert_manager/` | Raises and lists alerts; publishes `AlertRaised`; no second alert while one is still OPEN for the same rule and device |
| Notification Dispatcher | `alert_notification/notification_dispatcher/` | Push first; SMS, retried up to three times, when the push is not confirmed within 2 minutes (ADR-04) |
| Delivery Tracker | `alert_notification/delivery_tracker/` | Records every push and SMS attempt; reports the latest one as `deliveryStatus` |
| Farm Access Cache | `alert_notification/farm_access_cache/` | Local copy of farms and grants kept in step by `AccessGranted` / `AccessRevoked` events (ADR-05) |

`seed.py` replays four `TelemetryReceived` events through these components at start-up, so the seeded alerts are produced exactly as live ones would be. The push service and SMS gateway are in-memory stand-ins (`notification_dispatcher/channels.py`).

## Live alert flow (Runtime diagram 1)

```text
Event Broker ──TelemetryReceived──▶ Threshold Evaluator ──breach──▶ Alert Manager ──AlertRaised──▶ Event Broker
                                                                        │
                                                                        ▼
                                  Push Notification Service ◀── Notification Dispatcher ──▶ Delivery Tracker
                                                                        │  (push not confirmed in 2 min)
                                                                        ▼
                                                                   SMS Gateway
```
