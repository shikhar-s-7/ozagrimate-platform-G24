# OzAgriMate Platform: Assignment 4 prototype

A partial implementation of the OzAgriMate architecture (ISYS3459, Assignment 4). Three of the five services are coded in Python with FastAPI. They serve the eight endpoints in the report's API table. Every other container has a folder with a README describing what it would contain, because the brief does not require the user interface, the gateway, the broker or the databases to be built.

The folders follow the C4 diagrams in the report: one folder per **container**, and inside each coded service one Python package per **component**.

## Container diagram → folders

| Container | Folder | In this prototype |
|---|---|---|
| Farmer Mobile App | `clients/farmer-mobile-app/` | README only |
| Web Dashboard | `clients/web-dashboard/` | README only |
| API Gateway | `api-gateway/` | README only (routing table) |
| Telemetry Ingestion Service | `services/telemetry-ingestion-service/` | FastAPI app, port 8081, endpoints #1–3 |
| Alert & Notification Service | `services/alert-notification-service/` | FastAPI app, port 8082, endpoints #4–6 |
| Farm & Access Service | `services/farm-access-service/` | FastAPI app, port 8083, endpoints #7–8 |
| Irrigation Advisory Service | `services/irrigation-advisory-service/` | README only |
| Reporting & Compliance Service | `services/reporting-compliance-service/` | README only |
| Event Broker | `event-broker/` | README only (topics); in-memory publishers stand in |
| Telemetry Store, Alert DB, Farm & Access DB | inside each service | In-memory repositories seeded at start-up |

Code shared by every service lives in `libs/ozagrimate_common/`: the agreed error body and a UTC clock, and nothing else, so each service can still be deployed on its own.

## Component diagrams → packages

**Telemetry Ingestion Service** (`services/telemetry-ingestion-service/telemetry_ingestion/`)

| Component | Package | Responsibility |
|---|---|---|
| Telemetry API | `api/` | Endpoints #1–3 (FastAPI routers and Pydantic schemas) |
| Ingestion Pipeline | `ingestion_pipeline/` | Runs each batch through the components below, in order |
| Protocol Adapters | `protocol_adapters/` | HTTPS JSON and MQTT payloads → one canonical batch |
| Validator | `validator/` | Metric allowed for the device type, unit conversion, range and clock checks |
| Duplicate Filter | `duplicate_filter/` | Drops replayed readings by `deviceId` + `sequenceNo` |
| Reading Store | `reading_store/` | Saves accepted readings |
| Device Registry | `device_registry/` | Gateways, devices, health (offline after 30 min), configuration versions |
| Event Publisher | `event_publisher/` | Publishes `TelemetryReceived` to `telemetry.received`, keyed by `farmId` |

**Alert & Notification Service** (`services/alert-notification-service/alert_notification/`)

| Component | Package | Responsibility |
|---|---|---|
| Alert API | `api/` | Endpoints #4–6 (FastAPI routers and Pydantic schemas) |
| Rule Manager | `rule_manager/` | Alert thresholds stored as data per crop, region and metric (ADR-08) |
| Threshold Evaluator | `threshold_evaluator/` | Consumes `TelemetryReceived` and checks each reading against the farm's rules |
| Alert Manager | `alert_manager/` | Raises, stores and lists alerts; publishes `AlertRaised` to `alerts.raised`, keyed by `farmId` |
| Notification Dispatcher | `notification_dispatcher/` | Push first, SMS when the push is not confirmed within 2 minutes (ADR-04) |
| Delivery Tracker | `delivery_tracker/` | Records every push and SMS attempt and finds overdue pushes |
| Farm Access Cache | `farm_access_cache/` | Local copy of farms and grants from `AccessGranted` / `AccessRevoked`; checks who may read a farm's alerts (ADR-05) |

**Farm & Access Service** (`services/farm-access-service/farm_access/`)

| Component | Package | Responsibility |
|---|---|---|
| Access API | `api/` | Endpoints #7–8 (FastAPI router and Pydantic schemas) |
| Authorisation Checker | `authorisation_checker/` | Reads `X-User-Id`; only a farm's owner may change its grants |
| Grant Manager | `grant_manager/` | Creates and revokes grants; one active grant per agronomist per farm |
| Farm Registry | `farm_registry/` | Farms, owners and registered agronomists |
| Grant Event Publisher | `grant_event_publisher/` | Publishes `AccessGranted` / `AccessRevoked` to `access.grants`, keyed by `farmId` |

Each coded package follows the same layering: router (`api/`) → component service → in-memory repository. `main.py` in each service wires the components together in `create_app()`.

## Endpoints

| # | Method | URL | Service | Success | Error cases |
|---|---|---|---|---|---|
| 1 | POST | `/api/v1/telemetry/readings` | Telemetry Ingestion :8081 | 202 + acknowledgement | 400 malformed batch or unknown gateway; a resent batch is counted as duplicates |
| 2 | GET | `/api/v1/devices/{deviceId}/health` | Telemetry Ingestion :8081 | 200 | 404 unknown device |
| 3 | PUT | `/api/v1/devices/{deviceId}/configuration` | Telemetry Ingestion :8081 | 200 | 400 interval out of range; 404 unknown device |
| 4 | GET | `/api/v1/farms/{farmId}/alerts?status=OPEN` | Alert & Notification :8082 | 200 | 400 unknown status; 401 no `X-User-Id`; 403 no `READ_ALERTS` grant; 404 unknown farm |
| 5 | PUT | `/api/v1/alert-rules/{ruleId}` | Alert & Notification :8082 | 200 | 400 minimum not below maximum; 404 |
| 6 | DELETE | `/api/v1/alert-rules/{ruleId}` | Alert & Notification :8082 | 204 | 404 unknown rule (so a second delete answers 404) |
| 7 | POST | `/api/v1/farms/{farmId}/access-grants` | Farm & Access :8083 | 201 + `Location` | 400; 401 no `X-User-Id`; 403 not the owner; 404 farm or agronomist; 409 grant already active |
| 8 | DELETE | `/api/v1/farms/{farmId}/access-grants/{grantId}` | Farm & Access :8083 | 204 | 401; 403; 404 no active grant |

Each running service also serves interactive documentation at `/docs` (Swagger UI), generated from the same Pydantic models.

## Run it

Needs Python 3.11 or newer. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
./run_all.sh                       # Windows: run_all.bat
```

Then open http://localhost:8081/docs, http://localhost:8082/docs and http://localhost:8083/docs. To run one service on its own:

```bash
python -m uvicorn telemetry_ingestion.main:app --app-dir services/telemetry-ingestion-service --port 8081
```

## Test it

- **Automated:** `python -m pytest` from the repository root runs every service's tests.
- **Postman:** import `postman/OzAgriMate.postman_collection.json` and run it with the Collection Runner. The folders hold a success request and the error requests for each endpoint, with checks on every response. Data is in memory and seeded at start-up, so restart the services before a full run.

## Conventions

- URLs start with `/api/v1`, use plural nouns, and send and receive camelCase JSON with UTC ISO-8601 timestamps.
- Every error, from every service, has the same body. Invalid requests answer 400 (FastAPI's default 422 is mapped to 400):

  ```json
  {"timestamp": "2026-10-22T08:45:00Z", "status": 404, "error": "Not Found",
   "message": "Device DEV-9999 is not registered", "path": "/api/v1/devices/DEV-9999/health"}
  ```
- **Caller identity:** the API Gateway validates each caller's token with the Identity Provider and forwards the user ID in the `X-User-Id` header. Services trust that header because only the gateway can reach them. In Postman, set the header yourself.
- **Events:** services publish events to an in-memory outbox that stands in for the Kafka producer. Topics are listed in `event-broker/README.md`.

### Seed data

| Kind | IDs |
|---|---|
| Farms | `FARM-001` Riverbend Farm (owner `FARMER-001`, Riverina NSW, wheat); `FARM-002` Red Gum Orchard (owner `FARMER-002`, Riverland SA, almonds) |
| Gateways | `GW-01` on FARM-001; `GW-02` on FARM-002 |
| Devices | `DEV-1001` soil-moisture probe and `DEV-1002` weather station on GW-01 (online); `DEV-2001` water-flow meter on GW-02 (silent for two hours, so offline) |
| Agronomists | `AGR-001` Mallee Agronomy Services; `AGR-002` Coastal Crop Advisory |
| Access grants | `GRANT-001`: FARM-001 shared with AGR-002 (telemetry and alerts) |
| Alert rules | `RULE-001` wheat soil moisture 20–45 % (CRITICAL), `RULE-002` wheat air temperature 0–38 C, `RULE-005` wheat soil temperature 5–35 C (all RIVERINA-NSW); `RULE-003` almond soil moisture 25–50 %, `RULE-004` almond water flow 0–400 L/min (RIVERLAND-SA) |
| Alerts | Raised at start-up by replaying four readings through the Threshold Evaluator: on FARM-001 `ALERT-001` RESOLVED, `ALERT-002` ACKNOWLEDGED and `ALERT-003` OPEN (push not confirmed, so sent by SMS); on FARM-002 `ALERT-004` OPEN (push delivered) |

Device last-seen times are relative to start-up, so a device that starts online goes offline after 30 minutes without readings.

## Repository layout

```text
ozagrimate-platform/
├── README.md                 this file
├── requirements.txt          runtime packages (FastAPI, Uvicorn, shared library)
├── requirements-dev.txt      adds pytest and the test client
├── run_all.sh / run_all.bat  start the three services on ports 8081–8083
├── docs/                     Structurizr workspace and exported C4 diagrams
├── postman/                  Postman collection for all endpoints
├── libs/ozagrimate_common/   shared error body and UTC clock
├── clients/                  farmer-mobile-app/, web-dashboard/ (README only)
├── api-gateway/              README only
├── event-broker/             README only
└── services/
    ├── telemetry-ingestion-service/    port 8081
    ├── alert-notification-service/     port 8082
    ├── farm-access-service/            port 8083
    ├── irrigation-advisory-service/    README only
    └── reporting-compliance-service/   README only
```
