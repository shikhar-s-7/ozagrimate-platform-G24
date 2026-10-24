"""Farm Registry component.

Knows every farm, its owner, region and main crop, and the agronomists
registered on the platform. In production it reads the Farm & Access DB
(PostgreSQL); here an in-memory repository stands in for it.
"""

from .models import Agronomist, Farm
from .repository import InMemoryFarmRepository, seeded_farm_repository
from .service import FarmRegistry

__all__ = ["Agronomist", "Farm", "FarmRegistry", "InMemoryFarmRepository", "seeded_farm_repository"]
