"""Threshold Evaluator component.

Consumes TelemetryReceived events from the Event Broker and checks each reading
against the farm's alert rules (ASR2: alert within 5 minutes of a breach).
"""
