"""Validator component.

Checks each reading against what its device type can measure, converts it to the
canonical unit and rejects impossible values, so downstream services receive one
consistent format (ASR18). Rejecting out-of-range values is a first step towards
ASR23's anomaly detection.
"""

from .rules import METRIC_RULES, METRICS_BY_DEVICE_TYPE, ReadingRejected, ReadingValidator, RejectionReason

__all__ = ["METRIC_RULES", "METRICS_BY_DEVICE_TYPE", "ReadingRejected", "ReadingValidator", "RejectionReason"]
