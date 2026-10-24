"""Endpoint #4: GET /api/v1/farms/{farmId}/alerts?status=OPEN (to be implemented)."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/farms", tags=["Alert API"])

# Endpoint #4 goes here:
#   @router.get("/{farmId}/alerts", response_model=..., responses={400: ..., 404: ...})
#   200 with the farm's alerts; 400 for an unknown status value; 404 for an unknown farm.
