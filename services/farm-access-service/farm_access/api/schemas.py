"""Request and response bodies for endpoints #7-8 (camelCase JSON)."""

from __future__ import annotations

from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from ..grant_manager.models import Scope


class RequestModel(BaseModel):
    """Incoming JSON: camelCase keys, unknown keys rejected."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ResponseModel(BaseModel):
    """Outgoing JSON: camelCase keys."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ----- Endpoint #7: POST /api/v1/farms/{farmId}/access-grants -----

class AccessGrantRequest(RequestModel):
    agronomist_id: str = Field(min_length=1, max_length=64)
    scopes: list[Scope] = Field(min_length=1, max_length=4, description="What the agronomist may read.")
    expires_at: AwareDatetime | None = Field(default=None, description="Optional; must be in the future.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "agronomistId": "AGR-001",
                    "scopes": ["READ_TELEMETRY", "READ_ALERTS"],
                    "expiresAt": "2027-06-30T00:00:00Z",
                }
            ]
        }
    )

    @field_validator("scopes")
    @classmethod
    def scopes_are_unique(cls, scopes: list[Scope]) -> list[Scope]:
        if len(set(scopes)) != len(scopes):
            raise ValueError("must not repeat a scope")
        return scopes


class AccessGrantResponse(ResponseModel):
    grant_id: str
    farm_id: str
    agronomist_id: str
    agronomist_name: str
    scopes: list[Scope]
    status: str
    granted_by: str
    granted_at: datetime
    expires_at: datetime | None
