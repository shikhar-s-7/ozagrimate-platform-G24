"""In-memory stand-in for the farm and agronomist tables, with seed data."""

from __future__ import annotations

from collections.abc import Iterable

from .models import Agronomist, Farm


class InMemoryFarmRepository:
    def __init__(self, farms: Iterable[Farm], agronomists: Iterable[Agronomist]) -> None:
        self._farms = {farm.farm_id: farm for farm in farms}
        self._agronomists = {agronomist.agronomist_id: agronomist for agronomist in agronomists}

    def find_farm(self, farm_id: str) -> Farm | None:
        return self._farms.get(farm_id)

    def find_agronomist(self, agronomist_id: str) -> Agronomist | None:
        return self._agronomists.get(agronomist_id)


def seeded_farm_repository() -> InMemoryFarmRepository:
    farms = [
        Farm("FARM-001", "Riverbend Farm", "FARMER-001", "Riverina, NSW", "Wheat"),
        Farm("FARM-002", "Red Gum Orchard", "FARMER-002", "Riverland, SA", "Almonds"),
    ]
    agronomists = [
        Agronomist("AGR-001", "Mallee Agronomy Services"),
        Agronomist("AGR-002", "Coastal Crop Advisory"),
    ]
    return InMemoryFarmRepository(farms, agronomists)
