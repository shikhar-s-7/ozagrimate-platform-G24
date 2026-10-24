"""Alert & Notification Service (container, port 8082).

Evaluates incoming telemetry against per-crop, per-region alert rules, raises
alerts and delivers them by push notification with SMS fallback (ADR-04, ADR-08).
Each sub-package is one component in the component diagram
"Component: Alert & Notification Service".
"""
