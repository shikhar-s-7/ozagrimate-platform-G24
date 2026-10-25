"""Alert rules: one threshold band per crop type, region and metric."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

BELOW_MIN = "BELOW_MIN"
ABOVE_MAX = "ABOVE_MAX"


class Metric(str, Enum):
    """The metrics Telemetry Ingestion publishes, in their canonical units."""

    SOIL_MOISTURE = "SOIL_MOISTURE"
    SOIL_TEMPERATURE = "SOIL_TEMPERATURE"
    AIR_TEMPERATURE = "AIR_TEMPERATURE"
    RAINFALL = "RAINFALL"
    WATER_FLOW = "WATER_FLOW"


# Same canonical units as telemetry_ingestion/validator/rules.py, so a rule's
# limits compare directly with the values in TelemetryReceived events.
CANONICAL_UNITS: dict[str, str] = {
    "SOIL_MOISTURE": "%",
    "SOIL_TEMPERATURE": "C",
    "AIR_TEMPERATURE": "C",
    "RAINFALL": "mm",
    "WATER_FLOW": "L/min",
}


class Severity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class AlertRule:
    rule_id: str
    crop_type: str
    region: str
    metric: str
    min_value: float
    max_value: float
    severity: str
    version: int
    updated_at: datetime

    @property
    def unit(self) -> str:
        return CANONICAL_UNITS[self.metric]

    def applies_to(self, crop_type: str, region: str, metric: str) -> bool:
        return (self.crop_type, self.region, self.metric) == (crop_type, region, metric)

    def breach(self, value: float) -> str | None:
        """BELOW_MIN or ABOVE_MAX when the value is outside the band, otherwise None."""
        if value < self.min_value:
            return BELOW_MIN
        if value > self.max_value:
            return ABOVE_MAX
        return None

    def same_settings_as(
        self, crop_type: str, region: str, metric: str, min_value: float, max_value: float, severity: str
    ) -> bool:
        return (self.crop_type, self.region, self.metric, self.min_value, self.max_value, self.severity) == (
            crop_type,
            region,
            metric,
            min_value,
            max_value,
            severity,
        )
