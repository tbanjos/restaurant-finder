"""Composition of the default restaurant-search pipeline.

The pipeline is the application's central data flow:

    resolve cuisine -> build API filters -> fetch entries -> keep open stores
    -> map to models -> rank -> apply limit

``SearchRestaurants.execute`` is the application entry point around this
pipeline. New behaviour should normally be added as a stage in
:mod:`glovo_restaurants.application.steps` instead of growing an adapter class.
"""

from __future__ import annotations

from .pipeline import Pipeline
from .search_context import SearchContext
from .steps import (
    BuildFiltersStep,
    BuildRestaurantsStep,
    FetchStoreEntriesStep,
    FilterOpenStep,
    LimitResultsStep,
    RankRestaurantsStep,
    ResolveCuisineStep,
)


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
