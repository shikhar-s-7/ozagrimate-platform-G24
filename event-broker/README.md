# Event Broker (not implemented in this prototype)

**Container:** Event Broker · **Technology:** Apache Kafka (a managed service in an Australian region)

Services share events through the broker instead of calling each other, so a slow or failed consumer never blocks ingestion. In the prototype, each publisher component keeps its events in an in-memory list (`.published`) that stands in for the Kafka producer.

## Topics

| Topic | Events | Producer | Consumers |
|---|---|---|---|
| `telemetry.received` | `TelemetryReceived` | Telemetry Ingestion Service | Alert & Notification, Irrigation Advisory, Reporting & Compliance |
| `access.grants` | `AccessGranted`, `AccessRevoked` | Farm & Access Service | Alert & Notification |
| `alerts.raised` | `AlertRaised` | Alert & Notification Service | Irrigation Advisory |
| `recommendations.issued` | `RecommendationIssued` | Irrigation Advisory Service | Alert & Notification, Reporting & Compliance |

- **Message key:** every topic is keyed by `farmId`. Each farm's events stay in order on one partition, and consumers scale out by partition as the number of farms grows (ADR-02).
- **Event body:** every event carries `eventType` and `schemaVersion`, so its format can change without breaking consumers.
