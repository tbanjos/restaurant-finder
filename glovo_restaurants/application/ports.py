"""Ports implemented by outbound adapters.

The application core depends on these protocols rather than on HTTP, CSV, or
configuration details. Adapters supply concrete implementations at composition
time.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from ..domain import Location, Restaurant


@runtime_checkable
class RestaurantProvider(Protocol):
    """Source of cuisine metadata and raw Glovo store entries."""

    location: Location

    def resolve_cuisine(self, query: str) -> tuple[str, str]:
        """Resolve a cuisine query to a display name and filter id."""
        ...

    def cuisines(self) -> Mapping[str, tuple[str, str]]:
        """Return ``{normalized_name: (display_name, filter_id)}``."""
        ...

    def fetch_store_entries(
        self, filters: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Return every store entry matching ``filters``."""
        ...


@runtime_checkable
class RestaurantWriter(Protocol):
    """Destination for ranked restaurant results."""

    def write(self, restaurants: Sequence[Restaurant]) -> None:
        """Persist ``restaurants``."""
        ...
