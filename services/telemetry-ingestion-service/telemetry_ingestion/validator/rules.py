"""Validation and unit-normalisation rules for each metric and device type.

The rules are data, not code paths, so onboarding a new device type means adding
entries here rather than changing the pipeline (ASR26).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum

from ..protocol_adapters.base import CanonicalReading

MAX_CLOCK_SKEW = timedelta(minutes=5)


class RejectionReason(str, Enum):
    UNKNOWN_DEVICE = "UNKNOWN_DEVICE"
    UNSUPPORTED_METRIC = "UNSUPPORTED_METRIC"
    UNSUPPORTED_UNIT = "UNSUPPORTED_UNIT"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    FUTURE_TIMESTAMP = "FUTURE_TIMESTAMP"


class ReadingRejected(Exception):
    """One reading failed validation; the rest of the batch carries on."""

    def __init__(self, reason: RejectionReason, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


@dataclass(frozen=True)
class MetricRule:
    canonical_unit: str
    minimum: float
    maximum: float
    to_canonical: dict[str, Callable[[float], float]]


def _same(value: float) -> float:
    return value


def _fahrenheit_to_celsius(value: float) -> float:
    return (value - 32) * 5 / 9


METRIC_RULES: dict[str, MetricRule] = {
    "SOIL_MOISTURE": MetricRule("%", 0, 100, {"%": _same, "fraction": lambda v: v * 100}),
    "SOIL_TEMPERATURE": MetricRule("C", -20, 60, {"C": _same, "F": _fahrenheit_to_celsius}),
    "AIR_TEMPERATURE": MetricRule("C", -40, 60, {"C": _same, "F": _fahrenheit_to_celsius}),
    "RAINFALL": MetricRule("mm", 0, 500, {"mm": _same, "in": lambda v: v * 25.4}),
    "WATER_FLOW": MetricRule("L/min", 0, 10_000, {"L/min": _same, "gal/min": lambda v: v * 3.78541}),
}

METRICS_BY_DEVICE_TYPE: dict[str, frozenset[str]] = {
    "SOIL_MOISTURE_PROBE": frozenset({"SOIL_MOISTURE", "SOIL_TEMPERATURE"}),
    "WEATHER_STATION": frozenset({"AIR_TEMPERATURE", "RAINFALL"}),
    "WATER_FLOW_METER": frozenset({"WATER_FLOW"}),
}


def _number(value: float) -> str:
    return f"{value:g}"


class ReadingValidator:
    def normalise(self, reading: CanonicalReading, device_type: str, received_at: datetime) -> CanonicalReading:
        """Return the reading in its canonical unit, or raise ReadingRejected."""
        if reading.metric not in METRICS_BY_DEVICE_TYPE.get(device_type, frozenset()):
            raise ReadingRejected(
                RejectionReason.UNSUPPORTED_METRIC,
                f"A {device_type} does not report {reading.metric}",
            )

        rule = METRIC_RULES[reading.metric]
        convert = rule.to_canonical.get(reading.unit)
        if convert is None:
            allowed = ", ".join(rule.to_canonical)
            raise ReadingRejected(
                RejectionReason.UNSUPPORTED_UNIT,
                f"Unit '{reading.unit}' is not accepted for {reading.metric}; use one of: {allowed}",
            )

        value = round(convert(reading.value), 2)
        if not rule.minimum <= value <= rule.maximum:
            raise ReadingRejected(
                RejectionReason.OUT_OF_RANGE,
                f"{reading.metric} of {_number(value)} {rule.canonical_unit} is outside "
                f"{_number(rule.minimum)} to {_number(rule.maximum)} {rule.canonical_unit}",
            )

        if reading.captured_at > received_at + MAX_CLOCK_SKEW:
            raise ReadingRejected(
                RejectionReason.FUTURE_TIMESTAMP,
                "capturedAt is more than 5 minutes after the batch was received",
            )

        return replace(reading, value=value, unit=rule.canonical_unit)
