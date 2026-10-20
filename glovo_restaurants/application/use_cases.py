"""Application use cases.

Use cases orchestrate the domain and outbound ports. They know nothing about
HTTP, command-line arguments, property files, or CSV formatting.
"""

from __future__ import annotations

from .pipeline import Pipeline
from .ports import RestaurantProvider
from .search import build_search_pipeline
from .search_context import SearchContext
from ..domain import DEFAULT_SORT, Restaurant


class SearchRestaurants:
    """Return ranked open restaurants for a cuisine."""

    def __init__(
        self,
        provider: RestaurantProvider,
        pipeline: Pipeline[SearchContext] | None = None,
    ) -> None:
        self.provider = provider
        self.pipeline = pipeline or build_search_pipeline()

    def execute(
        self,
        cuisine: str,
        *,
        limit: int | None = 30,
        sort_by: str | None = None,
    ) -> list[Restaurant]:
        context = SearchContext(
            client=self.provider,
            cuisine=cuisine,
            limit=limit,
            sort_by=sort_by or DEFAULT_SORT,
        )
        return self.pipeline.run(context).restaurants


class ListCuisines:
    """List the cuisine names exposed by the restaurant provider."""

    def __init__(self, provider: RestaurantProvider) -> None:
        self.provider = provider

    def execute(self) -> list[str]:
        return sorted(name for name, _ in self.provider.cuisines().values())
