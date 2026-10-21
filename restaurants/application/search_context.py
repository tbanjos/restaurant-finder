"""Mutable state shared by restaurant search stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..domain import DEFAULT_SORT, Restaurant

if TYPE_CHECKING:
    from .ports import RestaurantProvider


@dataclass
class SearchContext:
    """Mutable state shared by every stage of a restaurant search."""

    client: "RestaurantProvider"
    cuisine: str
    limit: int | None = 30
    sort_by: str = DEFAULT_SORT
    restaurants: list[Restaurant] = field(default_factory=list)
