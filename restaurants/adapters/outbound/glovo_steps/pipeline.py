"""Composition of Glovo-specific search steps."""

from __future__ import annotations

from ....application.pipeline import Pipeline
from .build_filters import BuildFiltersStep
from .build_restaurants import BuildRestaurantsStep
from .context import GlovoSearchContext
from .fetch_store_entries import FetchStoreEntriesStep
from .filter_open import FilterOpenStep
from .resolve_cuisine import ResolveCuisineStep


def build_glovo_pipeline() -> Pipeline[GlovoSearchContext]:
    """Create the pipeline that turns a cuisine into Glovo restaurants."""
    return Pipeline(
        (
            ResolveCuisineStep(),
            BuildFiltersStep(),
            FetchStoreEntriesStep(),
            FilterOpenStep(),
            BuildRestaurantsStep(),
        )
    )
