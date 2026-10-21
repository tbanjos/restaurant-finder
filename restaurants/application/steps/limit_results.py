"""Apply the result limit after ranking."""

from __future__ import annotations

from ..search_context import SearchContext


class LimitResultsStep:
    """Apply the caller's result limit after ranking."""

    name = "limit-results"

    def run(self, context: SearchContext) -> None:
        if context.limit is not None:
            context.restaurants = context.restaurants[: context.limit]
