"""Composition of the default provider-neutral search pipeline.

The pipeline is the application's central data flow:

    fetch restaurants -> rank -> apply limit

Provider-specific concerns such as cuisine lookup, API filters, availability,
and response mapping belong to the outbound adapter. New application behaviour
should normally be added as a stage in
:mod:`glovo_restaurants.application.steps`.
"""

from __future__ import annotations

from .pipeline import Pipeline
from .search_context import SearchContext
from .steps import FetchRestaurantsStep, LimitResultsStep, RankRestaurantsStep


def build_search_pipeline() -> Pipeline[SearchContext]:
    """Create the default restaurant-search pipeline.

    Maintainers can compose a custom pipeline with any subset of the exported
    stages, or append their own stage that complies with ``PipelineStep``.
    """
    return Pipeline(
        (
            FetchRestaurantsStep(),
            RankRestaurantsStep(),
            LimitResultsStep(),
        )
    )
