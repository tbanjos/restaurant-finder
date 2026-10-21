"""Find restaurants by cuisine and export them as a ranked CSV."""

from .domain.errors import (
    AddressNotFoundError,
    CuisineNotFoundError,
    ProviderError,
)
from .domain import (
    SORT_OPTIONS,
    Location,
    Restaurant,
    parse_distance,
    parse_eta,
    parse_rating,
    parse_votes,
    sort_restaurants,
)
from .application.pipeline import Pipeline
from .application.pipeline_step import PipelineStep
from .application.ports import RestaurantProvider, RestaurantWriter
from .application.search import build_search_pipeline
from .application.search_context import SearchContext
from .application.cases import ListCuisines, SearchRestaurants
from .adapters.inbound.cli import main
from .adapters.outbound.config import get_settings, load_settings
from .adapters.outbound.configuration_error import ConfigurationError
from .adapters.outbound.csv_writer import CsvRestaurantWriter
from .adapters.outbound.settings import Settings

__all__ = [
    "AddressNotFoundError",
    "ConfigurationError",
    "CsvRestaurantWriter",
    "CuisineNotFoundError",
    "ListCuisines",
    "Location",
    "Pipeline",
    "PipelineStep",
    "ProviderError",
    "Restaurant",
    "RestaurantProvider",
    "RestaurantWriter",
    "SORT_OPTIONS",
    "SearchContext",
    "SearchRestaurants",
    "Settings",
    "build_search_pipeline",
    "get_settings",
    "load_settings",
    "main",
    "parse_distance",
    "parse_eta",
    "parse_rating",
    "parse_votes",
    "sort_restaurants",
]
