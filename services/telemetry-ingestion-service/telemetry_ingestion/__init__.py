"""Telemetry Ingestion Service (container, port 8081).

Receives sensor readings from farm gateways, normalises and de-duplicates them,
tracks device health and holds device configuration. Each sub-package is one
component in the component diagram "Component: Telemetry Ingestion Service".
"""
