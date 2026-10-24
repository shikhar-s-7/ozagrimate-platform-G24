# Reporting & Compliance Service (not implemented in this prototype)

**Container:** Reporting & Compliance Service · **Technology:** Python, FastAPI

The brief does not require this service to be coded. In the architecture it would:

- consume `TelemetryReceived` and `RecommendationIssued` events to build resource-usage figures per farm;
- generate a per-client resource-usage report on demand for farmers and agronomists (ASR11);
- generate regulator-ready reports on a schedule, in the formats regulators specify, and submit them to the Government & Regulatory Reporting System (ASR16, ASR29);
- keep generated reports in the Report Store (S3-compatible object storage);
- serve reports to the apps through the API Gateway.
