"""Rule Manager service: replace, delete and look up alert rules."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from ozagrimate_common import ApiError

from .models import AlertRule
from .repository import InMemoryRuleRepository


class RuleManager:
    def __init__(self, repository: InMemoryRuleRepository, clock: Callable[[], datetime]) -> None:
        self._repository = repository
        self._clock = clock

    def require_rule(self, rule_id: str) -> AlertRule:
        rule = self._repository.find(rule_id)
        if rule is None:
            raise ApiError(404, f"Alert rule {rule_id} does not exist")
        return rule

    def replace_rule(
        self,
        rule_id: str,
        *,
        crop_type: str,
        region: str,
        metric: str,
        min_value: float,
        max_value: float,
        severity: str,
    ) -> AlertRule:
        """Replace every field of an existing rule as a new version (ADR-08).

        PUT is idempotent: sending the values the rule already has changes
        nothing and returns the current version.
        """
        current = self.require_rule(rule_id)
        if current.same_settings_as(crop_type, region, metric, min_value, max_value, severity):
            return current
        rule = replace(
            current,
            crop_type=crop_type,
            region=region,
            metric=metric,
            min_value=min_value,
            max_value=max_value,
            severity=severity,
            version=current.version + 1,
            updated_at=self._clock(),
        )
        self._repository.save(rule)
        return rule

    def delete_rule(self, rule_id: str) -> None:
        self.require_rule(rule_id)
        self._repository.delete(rule_id)

    def rules_for(self, crop_type: str, region: str, metric: str) -> list[AlertRule]:
        """The rules the Threshold Evaluator applies to one reading."""
        return [rule for rule in self._repository.all() if rule.applies_to(crop_type, region, metric)]
