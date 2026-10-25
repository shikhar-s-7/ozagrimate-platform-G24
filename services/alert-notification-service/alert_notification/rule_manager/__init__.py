"""Rule Manager component.

Stores alert thresholds as data rules per crop type and region, so they change
through the API without redeploying (ADR-08, ASR14). Endpoints #5 and #6 use it.
In production it reads the Alert DB (PostgreSQL); here an in-memory repository
stands in for it.
"""

from .models import ABOVE_MAX, BELOW_MIN, CANONICAL_UNITS, AlertRule, Metric, Severity
from .repository import InMemoryRuleRepository, seeded_rule_repository
from .service import RuleManager

__all__ = [
    "ABOVE_MAX",
    "BELOW_MIN",
    "CANONICAL_UNITS",
    "AlertRule",
    "InMemoryRuleRepository",
    "Metric",
    "RuleManager",
    "Severity",
    "seeded_rule_repository",
]
