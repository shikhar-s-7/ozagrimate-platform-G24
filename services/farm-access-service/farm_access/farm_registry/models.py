"""Farms and agronomists."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Farm:
    farm_id: str
    name: str
    owner_id: str
    region: str
    main_crop: str


@dataclass(frozen=True)
class Agronomist:
    agronomist_id: str
    name: str
