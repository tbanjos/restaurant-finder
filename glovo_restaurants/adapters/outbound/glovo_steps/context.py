"""Mutable state used only by the Glovo search pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ....domain import Restaurant

if TYPE_CHECKING:
    from ..glovo_client import GlovoClient


@dataclass
class GlovoSearchContext:
    """Intermediate Glovo-specific data produced while fetching restaurants."""

    client: "GlovoClient"
    cuisine: str
    filter_id: str | None = None
    filters: list[dict[str, Any]] = field(default_factory=list)
    entries: list[dict[str, Any]] = field(default_factory=list)
    restaurants: list[Restaurant] = field(default_factory=list)
