"""Endpoints #5 and #6: replace and delete an alert rule."""

from fastapi import APIRouter, Depends, Path, Response, status
from ozagrimate_common import ErrorBody

from ..rule_manager.models import AlertRule
from ..rule_manager.service import RuleManager
from .dependencies import get_rule_manager, require_rule_editor
from .schemas import AlertRuleRequest, AlertRuleResponse

# Every rule change needs an agronomist or operations staff caller.
router = APIRouter(
    prefix="/api/v1/alert-rules",
    tags=["Alert API"],
    dependencies=[Depends(require_rule_editor)],
    responses={
        401: {"model": ErrorBody, "description": "No X-User-Id header"},
        403: {"model": ErrorBody, "description": "Caller is not an agronomist or operations staff"},
    },
)


def _to_response(rule: AlertRule) -> AlertRuleResponse:
    return AlertRuleResponse(
        rule_id=rule.rule_id,
        crop_type=rule.crop_type,
        region=rule.region,
        metric=rule.metric,
        unit=rule.unit,
        min_value=rule.min_value,
        max_value=rule.max_value,
        severity=rule.severity,
        version=rule.version,
        updated_at=rule.updated_at,
    )


@router.put(
    "/{ruleId}",
    response_model=AlertRuleResponse,
    summary="Replace an alert rule's crop, region, metric, limits and severity",
    responses={
        400: {"model": ErrorBody, "description": "minValue not below maxValue, or another invalid field"},
        404: {"model": ErrorBody, "description": "Unknown rule"},
    },
)
def replace_alert_rule(
    body: AlertRuleRequest,
    rule_id: str = Path(alias="ruleId", examples=["RULE-001"]),
    rules: RuleManager = Depends(get_rule_manager),
) -> AlertRuleResponse:
    """The new limits apply to the next reading the Threshold Evaluator checks,
    with no redeployment (ADR-08, ASR14). Each change raises the version."""
    rule = rules.replace_rule(
        rule_id,
        crop_type=body.crop_type,
        region=body.region,
        metric=body.metric.value,
        min_value=body.min_value,
        max_value=body.max_value,
        severity=body.severity.value,
    )
    return _to_response(rule)


@router.delete(
    "/{ruleId}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete an alert rule",
    responses={404: {"model": ErrorBody, "description": "Unknown rule, so a second delete answers 404"}},
)
def delete_alert_rule(
    rule_id: str = Path(alias="ruleId", examples=["RULE-005"]),
    rules: RuleManager = Depends(get_rule_manager),
) -> Response:
    """Readings are no longer checked against the rule. Alerts it already raised are kept."""
    rules.delete_rule(rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
