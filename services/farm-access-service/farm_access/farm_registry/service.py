"""Farm Registry service: farm and agronomist lookups that answer 404 when missing."""

from __future__ import annotations

from ozagrimate_common import ApiError

from .models import Agronomist, Farm
from .repository import InMemoryFarmRepository


class FarmRegistry:
    def __init__(self, repository: InMemoryFarmRepository) -> None:
        self._repository = repository

    def require_farm(self, farm_id: str) -> Farm:
        farm = self._repository.find_farm(farm_id)
        if farm is None:
            raise ApiError(404, f"Farm {farm_id} does not exist")
        return farm

    def require_agronomist(self, agronomist_id: str) -> Agronomist:
        agronomist = self._repository.find_agronomist(agronomist_id)
        if agronomist is None:
            raise ApiError(404, f"Agronomist {agronomist_id} is not registered")
        return agronomist
