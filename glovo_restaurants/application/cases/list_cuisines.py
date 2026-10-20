"""Use case for listing available cuisines."""

from __future__ import annotations

from ..ports import RestaurantProvider


class ListCuisines:
    """List the cuisine names exposed by the restaurant provider."""

    def __init__(self, provider: RestaurantProvider) -> None:
        self.provider = provider

    def execute(self) -> list[str]:
        return sorted(name for name, _ in self.provider.cuisines().values())
