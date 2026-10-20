"""Restaurant search pipeline.

The pipeline is the application's central data flow:

    resolve cuisine -> build API filters -> fetch entries -> keep open stores
    -> map to models -> rank -> apply limit

``SearchRestaurants.execute`` is the application entry point around this
pipeline. New behaviour should normally be added as a stage instead of growing
an adapter class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..domain import DEFAULT_SORT, Restaurant, sort_restaurants
from .pipeline import Pipeline

if TYPE_CHECKING:
    from .ports import RestaurantProvider


@dataclass
class SearchContext:
    """Mutable state shared by every stage of a restaurant search."""

    client: "RestaurantProvider"
    cuisine: str
    limit: int | None = 30
    sort_by: str = DEFAULT_SORT
    filter_id: str | None = None
    filters: list[dict[str, Any]] = field(default_factory=list)
    entries: list[dict[str, Any]] = field(default_factory=list)
    restaurants: list[Restaurant] = field(default_factory=list)


class ResolveCuisineStep:
    """Resolve the user's cuisine text to a Glovo food-type filter id."""

    name = "resolve-cuisine"

    def run(self, context: SearchContext) -> None:
        _, context.filter_id = context.client.resolve_cuisine(context.cuisine)


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


class FetchStoreEntriesStep:
    """Fetch all store-wall entries matching the filters."""

    name = "fetch-store-entries"

    def run(self, context: SearchContext) -> None:
        context.entries = context.client.fetch_store_entries(context.filters)


class FilterOpenStep:
    """Drop entries that Glovo reports as unavailable for ordering."""

    name = "filter-open"

    def run(self, context: SearchContext) -> None:
        context.entries = [
            entry for entry in context.entries if store_is_open(entry)
        ]


class BuildRestaurantsStep:
    """Convert raw Glovo entries into the application's ``Restaurant`` model."""

    name = "build-restaurants"

    def run(self, context: SearchContext) -> None:
        client = context.client
        context.restaurants = [
            Restaurant.from_api(
                entry,
                city=client.city_name,
                country=client.country_code,
                language=client.language,
            )
            for entry in context.entries
        ]


class RankRestaurantsStep:
    """Rank restaurants using the context's ``sort_by`` strategy."""

    name = "rank-restaurants"

    def run(self, context: SearchContext) -> None:
        context.restaurants = sort_restaurants(
            context.restaurants, by=context.sort_by
        )


class LimitResultsStep:
    """Apply the caller's result limit after ranking."""

    name = "limit-results"

    def run(self, context: SearchContext) -> None:
        if context.limit is not None:
            context.restaurants = context.restaurants[: context.limit]


def store_is_open(entry: dict[str, Any]) -> bool:
    """Return whether a store listing is currently open for orders.

    Glovo omits ``availability`` from some responses; in that case the store is
    treated as open so older/partial payloads keep working.
    """
    status = (entry.get("availability") or {}).get("status")
    return status is None or str(status).upper() == "OPEN"


def build_search_pipeline() -> Pipeline[SearchContext]:
    """Create the default restaurant-search pipeline.

    Maintainers can compose a custom pipeline with any subset of the exported
    stages, or append their own stage that complies with ``PipelineStep``.
    """
    return Pipeline(
        (
            ResolveCuisineStep(),
            BuildFiltersStep(),
            FetchStoreEntriesStep(),
            FilterOpenStep(),
            BuildRestaurantsStep(),
            RankRestaurantsStep(),
            LimitResultsStep(),
        )
    )
