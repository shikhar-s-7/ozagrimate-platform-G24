"""Endpoints #7 and #8: grant and revoke an agronomist's access to a farm."""

from fastapi import APIRouter, Depends, Header, Path, Response, status
from ozagrimate_common import ErrorBody

from ..grant_manager.service import GrantManager
from .dependencies import get_grant_manager
from .schemas import AccessGrantRequest, AccessGrantResponse

router = APIRouter(prefix="/api/v1/farms", tags=["Access API"])

USER_ID_HEADER = Header(
    default=None,
    alias="X-User-Id",
    description="Set by the API Gateway after it validates the caller's token (ADR-05).",
    examples=["FARMER-001"],
)


@router.post(
    "/{farmId}/access-grants",
    status_code=status.HTTP_201_CREATED,
    response_model=AccessGrantResponse,
    summary="Grant an agronomist scoped access to a farm's data",
    responses={
        400: {"model": ErrorBody, "description": "Invalid body or expiresAt not in the future"},
        401: {"model": ErrorBody, "description": "No X-User-Id header"},
        403: {"model": ErrorBody, "description": "Caller does not own the farm"},
        404: {"model": ErrorBody, "description": "Unknown farm or agronomist"},
        409: {"model": ErrorBody, "description": "Agronomist already has an active grant on the farm"},
    },
)
def create_access_grant(
    body: AccessGrantRequest,
    response: Response,
    farm_id: str = Path(alias="farmId", examples=["FARM-001"]),
    user_id: str | None = USER_ID_HEADER,
    grants: GrantManager = Depends(get_grant_manager),
) -> AccessGrantResponse:
    """Only the farm's owner may grant access, and an agronomist holds at most
    one active grant per farm (ASR7, ASR9)."""
    grant = grants.create_grant(
        caller_id=user_id,
        farm_id=farm_id,
        agronomist_id=body.agronomist_id,
        scopes=[scope.value for scope in body.scopes],
        expires_at=body.expires_at,
    )
    response.headers["Location"] = f"/api/v1/farms/{grant.farm_id}/access-grants/{grant.grant_id}"
    return AccessGrantResponse(
        grant_id=grant.grant_id,
        farm_id=grant.farm_id,
        agronomist_id=grant.agronomist_id,
        agronomist_name=grant.agronomist_name,
        scopes=list(grant.scopes),
        status=grant.status,
        granted_by=grant.granted_by,
        granted_at=grant.granted_at,
        expires_at=grant.expires_at,
    )


@router.delete(
    "/{farmId}/access-grants/{grantId}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Revoke an agronomist's access to a farm",
    responses={
        401: {"model": ErrorBody, "description": "No X-User-Id header"},
        403: {"model": ErrorBody, "description": "Caller does not own the farm"},
        404: {"model": ErrorBody, "description": "Unknown farm, or no active grant with that ID"},
    },
)
def revoke_access_grant(
    farm_id: str = Path(alias="farmId", examples=["FARM-001"]),
    grant_id: str = Path(alias="grantId", examples=["GRANT-001"]),
    user_id: str | None = USER_ID_HEADER,
    grants: GrantManager = Depends(get_grant_manager),
) -> Response:
    """The grant is kept as REVOKED for the audit trail, and an AccessRevoked
    event tells other services to stop sharing data at once."""
    grants.revoke_grant(caller_id=user_id, farm_id=farm_id, grant_id=grant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
