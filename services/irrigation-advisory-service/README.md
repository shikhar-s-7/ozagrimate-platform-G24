# Irrigation Advisory Service (not implemented in this prototype)

**Container:** Irrigation Advisory Service · **Technology:** Python, FastAPI, ML model

The brief does not require this service to be coded. In the architecture it would:

- consume `TelemetryReceived` and `AlertRaised` events from the Event Broker and produce an irrigation recommendation within 1 minute of new sensor data (ASR22);
- fetch forecasts from the Weather Data Provider on a schedule (ASR28);
- use models tuned per crop type and climate zone (ASR24);
- store each recommendation with its input data and a plain-language rationale in the Advisory DB, for traceability (ASR25, R6);
- publish `RecommendationIssued` events, and send approved watering schedules to the Irrigation Control System;
- serve recommendations to the apps through the API Gateway.
