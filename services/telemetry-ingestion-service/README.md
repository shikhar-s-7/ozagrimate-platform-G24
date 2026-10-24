# Telemetry Ingestion Service

**Container:** Telemetry Ingestion Service · **Port:** 8081 · **Endpoints:** #1–3

Receives sensor readings from farm gateways, normalises and de-duplicates them, tracks whether each device is still reporting, and holds each device's configuration.

```bash
# from the repository root
python -m uvicorn telemetry_ingestion.main:app --app-dir services/telemetry-ingestion-service --port 8081
```

## Endpoints

| # | Method and URL | Success | Errors |
|---|---|---|---|
| 1 | `POST /api/v1/telemetry/readings` | 202 with a per-batch acknowledgement | 400 malformed batch or unregistered gateway |
| 2 | `GET /api/v1/devices/{deviceId}/health` | 200, `ONLINE` or `OFFLINE` | 404 unknown device |
| 3 | `PUT /api/v1/devices/{deviceId}/configuration` | 200, new configuration version | 400 interval out of range; 404 unknown device |

## Components → packages

| Component | Package |
|---|---|
| Telemetry API | `telemetry_ingestion/api/` |
| Ingestion Pipeline | `telemetry_ingestion/ingestion_pipeline/` |
| Protocol Adapters | `telemetry_ingestion/protocol_adapters/` |
| Validator | `telemetry_ingestion/validator/` |
| Duplicate Filter | `telemetry_ingestion/duplicate_filter/` |
| Reading Store | `telemetry_ingestion/reading_store/` |
| Device Registry | `telemetry_ingestion/device_registry/` |
| Event Publisher | `telemetry_ingestion/event_publisher/` |

## How a batch is processed (endpoint #1)

1. **Protocol Adapters** turn the payload into a canonical batch. Gateways can send JSON over HTTPS or compact rows over MQTT. The MQTT adapter is covered by unit tests, because the MQTT broker is outside this prototype.
2. **Device Registry** confirms the gateway is registered (400 if not) and, for each reading, that the device belongs to that gateway.
3. **Duplicate Filter** skips any reading whose `deviceId` + `sequenceNo` was already accepted. Gateways can therefore replay what they buffered while offline without creating duplicates.
4. **Validator** checks that the device type measures that metric, converts the value to the canonical unit, and rejects impossible values and timestamps more than 5 minutes in the future.

   | Metric | Canonical unit and range | Other unit accepted |
   |---|---|---|
   | `SOIL_MOISTURE` | % (0–100) | `fraction` |
   | `SOIL_TEMPERATURE` | C (−20 to 60) | `F` |
   | `AIR_TEMPERATURE` | C (−40 to 60) | `F` |
   | `RAINFALL` | mm (0–500) | `in` |
   | `WATER_FLOW` | L/min (0–10,000) | `gal/min` |

5. **Reading Store** saves each accepted reading.
6. **Device Registry** records contact with every device in the batch; this is what `/health` reports.
7. **Event Publisher** publishes one `TelemetryReceived` event for the accepted readings. Its topic is `telemetry.received` and its key is `farmId`.

The acknowledgement lists how many readings were accepted, duplicated or rejected, with a reason for each rejection.

## Design notes

- The pipeline keeps no state of its own; the store and the duplicate key would live in the Telemetry Store. Ingestion instances can therefore be added behind a load balancer as farms grow (ADR-02).
- New device types and units are data in `validator/rules.py`, and new protocols are new adapters. Neither needs a pipeline change (ADR-03).
- `PUT` is idempotent: sending a device the configuration it already has changes nothing. A real change creates a new version marked `PENDING_DEVICE_SYNC`, which the gateway pushes on the device's next connection.
