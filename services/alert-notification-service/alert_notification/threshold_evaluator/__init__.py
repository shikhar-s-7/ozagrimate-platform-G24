"""Threshold Evaluator component.

Consumes TelemetryReceived events from the Event Broker and checks each reading
against the farm's alert rules (ASR2: alert within 5 minutes of a breach).
Each breach goes to the Alert Manager, and each new alert to the Notification
Dispatcher.
"""

from .evaluator import ThresholdEvaluator

__all__ = ["ThresholdEvaluator"]
