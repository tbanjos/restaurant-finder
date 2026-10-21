"""Resolve the requested cuisine to a Glovo filter id."""

from __future__ import annotations

from .context import GlovoSearchContext


class ResolveCuisineStep:
    """Resolve the user's cuisine text to a Glovo food-type filter id."""

    name = "resolve-cuisine"

    def run(self, context: GlovoSearchContext) -> None:
        _, context.filter_id = context.client.resolve_cuisine(context.cuisine)
