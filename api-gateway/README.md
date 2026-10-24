# API Gateway (not implemented in this prototype)

**Container:** API Gateway · **Technology:** NGINX

The single entry point for the mobile app and the web dashboard. The brief does not require it to be built: in the prototype, clients and Postman call each service on its own port. In the architecture the gateway:

- terminates TLS for every client call;
- validates each caller's access token with the Identity Provider (OIDC) and checks the caller's role (ADR-05, ASR17);
- removes any `X-User-Id` header a client sent, then forwards the validated user ID in `X-User-Id` (services rely on this header);
- rate-limits each client;
- routes each `/api/v1` path to its service.

## Routing table

| Path | Service | Prototype address |
|---|---|---|
| `/api/v1/devices/**` | Telemetry Ingestion Service | http://localhost:8081 |
| `/api/v1/farms/{farmId}/alerts` | Alert & Notification Service | http://localhost:8082 |
| `/api/v1/alert-rules/**` | Alert & Notification Service | http://localhost:8082 |
| `/api/v1/farms/{farmId}/access-grants/**` | Farm & Access Service | http://localhost:8083 |
| `/api/v1/recommendations/**` | Irrigation Advisory Service | not built |
| `/api/v1/reports/**` | Reporting & Compliance Service | not built |

Farm gateways do not come through here. They send readings straight to the Telemetry Ingestion Service, at `POST /api/v1/telemetry/readings` or over MQTT, each authenticating with its own API key (ASR15). This keeps high-volume device traffic away from user requests.
