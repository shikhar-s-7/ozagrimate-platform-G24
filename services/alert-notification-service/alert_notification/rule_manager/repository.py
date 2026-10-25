"""In-memory stand-in for the alert-rule table in the Alert DB, with seed data."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from .models import AlertRule


class InMemoryRuleRepository:
    def __init__(self, rules: Iterable[AlertRule]) -> None:
        self._rules = {rule.rule_id: rule for rule in rules}

    def find(self, rule_id: str) -> AlertRule | None:
        return self._rules.get(rule_id)

    def save(self, rule: AlertRule) -> None:
        self._rules[rule.rule_id] = rule

    def delete(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    def all(self) -> list[AlertRule]:
        return list(self._rules.values())


def seeded_rule_repository(now: datetime) -> InMemoryRuleRepository:
    """Thresholds for the two seeded farms: wheat in the Riverina and almonds in the Riverland."""
    set_up = now - timedelta(days=60)
    return InMemoryRuleRepository(
        [
            AlertRule("RULE-001", "WHEAT", "RIVERINA-NSW", "SOIL_MOISTURE", 20.0, 45.0, "CRITICAL", 1, set_up),
            AlertRule("RULE-002", "WHEAT", "RIVERINA-NSW", "AIR_TEMPERATURE", 0.0, 38.0, "WARNING", 1, set_up),
            AlertRule("RULE-003", "ALMONDS", "RIVERLAND-SA", "SOIL_MOISTURE", 25.0, 50.0, "CRITICAL", 1, set_up),
            AlertRule("RULE-004", "ALMONDS", "RIVERLAND-SA", "WATER_FLOW", 0.0, 400.0, "WARNING", 1, set_up),
            AlertRule("RULE-005", "WHEAT", "RIVERINA-NSW", "SOIL_TEMPERATURE", 5.0, 35.0, "WARNING", 1, set_up),
        ]
    )
