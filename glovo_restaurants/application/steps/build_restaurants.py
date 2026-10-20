"""Map raw Glovo entries to the restaurant domain model."""

from __future__ import annotations

from ...domain import Restaurant
from ..search_context import SearchContext


class BuildRestaurantsStep:
    """Convert raw Glovo entries into the application's ``Restaurant`` model."""

    name = "build-restaurants"

    def run(self, context: SearchContext) -> None:
        location = context.client.location
        context.restaurants = [
            Restaurant.from_api(
                entry,
                city=location.city_name,
                country=location.country_code,
                language=location.language,
            )
            for entry in context.entries
        ]
