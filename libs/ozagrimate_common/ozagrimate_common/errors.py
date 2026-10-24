"""The agreed error body for every OzAgriMate endpoint.

Every error response, from any service, has this JSON shape::

    {
      "timestamp": "2026-10-22T08:45:00Z",
      "status": 404,
      "error": "Not Found",
      "message": "Device DEV-9999 is not registered",
      "path": "/api/v1/devices/DEV-9999/health"
    }

FastAPI answers an invalid request with 422 and a ``detail`` list by default.
The team's API table promises 400 with the body above, so
``register_error_handlers`` turns request-validation errors into 400.
"""

from __future__ import annotations

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from .timeutil import utc_now


class ErrorBody(BaseModel):
    """Schema of the agreed error body, shown in each service's /docs page."""

    timestamp: str
    status: int
    error: str
    message: str
    path: str


class ApiError(Exception):
    """Raise from any component to answer with the agreed error body."""

    def __init__(self, status: int, message: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.headers = headers


def error_body(status: int, message: str, path: str) -> dict:
    """Build the agreed error body."""
    return {
        "timestamp": utc_now().isoformat().replace("+00:00", "Z"),
        "status": status,
        "error": HTTPStatus(status).phrase,
        "message": message,
        "path": path,
    }


def _describe(exc: RequestValidationError) -> str:
    """Turn Pydantic's validation errors into one readable message."""
    parts = []
    for err in exc.errors():
        if err.get("type") == "json_invalid":
            parts.append("Request body is not valid JSON")
            continue
        location = ".".join(str(part) for part in err.get("loc", ()) if part != "body")
        if not location and err.get("type") == "missing":
            parts.append("Request body is required")
            continue
        message = str(err.get("msg", "is invalid")).removeprefix("Value error, ")
        parts.append(f"{location}: {message}" if location else message)
    return "; ".join(parts) or "The request is invalid"


def _hide_default_422(app: FastAPI) -> None:
    """Drop FastAPI's default 422 entries from the OpenAPI docs, since we answer 400."""
    build_schema = app.openapi

    def openapi() -> dict:
        if app.openapi_schema is None:
            schema = build_schema()
            for operations in schema.get("paths", {}).values():
                for operation in operations.values():
                    if isinstance(operation, dict):
                        operation.get("responses", {}).pop("422", None)
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = openapi


def register_error_handlers(app: FastAPI) -> None:
    """Make every error from this app use the agreed error body."""

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content=error_body(exc.status, exc.message, request.url.path),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_body(400, _describe(exc), request.url.path),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        default = HTTPStatus(exc.status_code).phrase
        message = exc.detail if isinstance(exc.detail, str) else default
        if message == default and exc.status_code == 404:
            message = f"No endpoint matches {request.method} {request.url.path}"
        elif message == default and exc.status_code == 405:
            message = f"{request.method} is not allowed on {request.url.path}"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.status_code, message, request.url.path),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_body(500, "Unexpected server error", request.url.path),
        )

    _hide_default_422(app)
