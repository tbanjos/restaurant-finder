"""Rank restaurants using the requested strategy."""

from __future__ import annotations

from ...domain import sort_restaurants
from ..search_context import SearchContext


class RankRestaurantsStep:
    """Rank restaurants using the context's ``sort_by`` strategy."""

    name = "rank-restaurants"

    def run(self, context: SearchContext) -> None:
        context.restaurants = sort_restaurants(
            context.restaurants, by=context.sort_by
        )
