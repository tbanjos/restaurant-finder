"""Ports implemented by outbound adapters.

The application core depends on these protocols rather than on HTTP, CSV, or
configuration details. Adapters supply concrete implementations at composition
time, so providers other than Glovo only need to implement this interface.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from ..domain import Location, Restaurant


@runtime_checkable
class RestaurantProvider(Protocol):
    """Provider-neutral source of restaurants and cuisine metadata."""

    location: Location

    def cuisine_names(self) -> list[str]:
        """Return the display names of the available cuisines."""
        ...

    def find_restaurants(self, cuisine: str) -> list[Restaurant]:
        """Return open restaurants matching ``cuisine`` in provider order."""
        ...


@runtime_checkable
class RestaurantWriter(Protocol):
    """Destination for ranked restaurant results."""

    def write(self, restaurants: Sequence[Restaurant]) -> None:
        """Persist ``restaurants``."""
        ...
