"""Fetch provider-neutral restaurants for the requested cuisine."""

from __future__ import annotations

from ..search_context import SearchContext


class FetchRestaurantsStep:
    """Ask the configured provider for restaurants matching the cuisine."""

    name = "fetch-restaurants"

    def run(self, context: SearchContext) -> None:
        context.restaurants = context.client.find_restaurants(context.cuisine)
