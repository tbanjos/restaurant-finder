"""Build the filter payload sent to Glovo's store wall."""

from __future__ import annotations

from ..search_context import SearchContext


class BuildFiltersStep:
    """Build the filter payload sent to Glovo's store wall."""

    name = "build-filters"

    def run(self, context: SearchContext) -> None:
        if context.filter_id is None:
            raise RuntimeError("resolve-cuisine must run before build-filters")
        context.filters = [
            {
                "filterId": "ADMIN_FILTERS",
                "filterAttributeIds": [context.filter_id],
            },
            {"filterId": "SORT_BY", "filterAttributeIds": ["RATING"]},
        ]
