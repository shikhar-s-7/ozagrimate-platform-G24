"""Farm & Access Service: the FastAPI app (port 8083).

Run from the repository root:
    python -m uvicorn farm_access.main:app --app-dir services/farm-access-service --port 8083
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from fastapi import FastAPI
from ozagrimate_common import register_error_handlers, utc_now

from .api.access_grant_routes import router as access_grant_router
from .authorisation_checker.checker import AuthorisationChecker
from .farm_registry.repository import seeded_farm_repository
from .farm_registry.service import FarmRegistry
from .grant_event_publisher.publisher import InMemoryGrantEventPublisher
from .grant_manager.repository import seeded_grant_repository
from .grant_manager.service import GrantManager


def create_app(clock: Callable[[], datetime] = utc_now) -> FastAPI:
    """Build the app and wire its components with fresh in-memory data."""
    app = FastAPI(
        title="OzAgriMate - Farm & Access Service",
        version="1.0.0",
        description=(
            "Endpoints #7-8: a farm owner grants an agronomist access to farm data, "
            "and revokes it. The API Gateway sets the X-User-Id header after validating the caller's token."
        ),
    )
    register_error_handlers(app)

    farms = FarmRegistry(seeded_farm_repository())
    events = InMemoryGrantEventPublisher()
    grant_manager = GrantManager(
        grants=seeded_grant_repository(clock()),
        farms=farms,
        checker=AuthorisationChecker(),
        publisher=events,
        clock=clock,
    )

    app.state.farms = farms
    app.state.events = events
    app.state.grant_manager = grant_manager

    app.include_router(access_grant_router)
    return app


app = create_app()
