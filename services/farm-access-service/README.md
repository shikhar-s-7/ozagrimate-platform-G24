# Farm & Access Service

**Container:** Farm & Access Service · **Port:** 8083 · **Endpoints:** #7–8

Holds farms, their owners and the agronomists on the platform. Farm owners use it to grant an agronomist scoped access to their farm's data, and to revoke that access.

```bash
# from the repository root
python -m uvicorn farm_access.main:app --app-dir services/farm-access-service --port 8083
```

## Endpoints

| # | Method and URL | Success | Errors |
|---|---|---|---|
| 7 | `POST /api/v1/farms/{farmId}/access-grants` | 201, grant body and `Location` header | 400 invalid body or past `expiresAt`; 401 no `X-User-Id`; 403 caller does not own the farm; 404 unknown farm or agronomist; 409 agronomist already has an active grant |
| 8 | `DELETE /api/v1/farms/{farmId}/access-grants/{grantId}` | 204, no body | 401; 403; 404 unknown farm or no active grant with that ID |

Both endpoints need the `X-User-Id` header. In production the API Gateway sets it after validating the caller's token, so a client cannot choose its own identity.

Checks run in a fixed order:
- **#7:** caller (401), farm (404), owner (403), expiry (400), agronomist (404), existing grant (409).
- **#8:** caller (401), farm (404), owner (403), active grant (404).

## Components → packages

| Component | Package |
|---|---|
| Access API | `farm_access/api/` |
| Authorisation Checker | `farm_access/authorisation_checker/` |
| Grant Manager | `farm_access/grant_manager/` |
| Farm Registry | `farm_access/farm_registry/` |
| Grant Event Publisher | `farm_access/grant_event_publisher/` |

## Design notes

- **Scopes:** a grant names what the agronomist may read: `READ_TELEMETRY`, `READ_ALERTS`, `READ_RECOMMENDATIONS` or `READ_REPORTS`. It can carry an expiry time; an expired grant stops counting as active.
- **Soft revoke:** revoking marks the grant `REVOKED` with who revoked it and when, rather than deleting it, so there is a record of who could see a farm's data.
- **Events:** every change publishes `AccessGranted` or `AccessRevoked` to `access.grants`, keyed by `farmId`. Other services, such as Alert & Notification, act on the change without calling this service.
