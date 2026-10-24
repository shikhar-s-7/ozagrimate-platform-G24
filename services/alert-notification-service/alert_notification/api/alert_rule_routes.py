"""Endpoints #5 and #6: replace and delete an alert rule (to be implemented)."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/alert-rules", tags=["Alert API"])

# Endpoint #5 goes here:
#   @router.put("/{ruleId}", response_model=..., responses={400: ..., 404: ...})
#   200 with the replaced rule; 400 when the minimum is not below the maximum; 404 for an unknown rule.
#
# Endpoint #6 goes here:
#   @router.delete("/{ruleId}", status_code=204, response_class=Response, responses={404: ...})
#   204 on success; 404 for an unknown rule (so a second delete answers 404).
