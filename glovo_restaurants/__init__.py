"""Find Glovo restaurants by cuisine and export them as a ranked CSV."""

from .domain.errors import (
    AddressNotFoundError,
    CuisineNotFoundError,
    GlovoError,
)
from .domain.models import (
    SORT_OPTIONS,
    Restaurant,
    parse_distance,
    parse_eta,
    parse_rating,
    parse_votes,
    sort_restaurants,
)
from .application.pipeline import Pipeline, PipelineStep
from .application.ports import RestaurantProvider, RestaurantWriter
from .application.search import SearchContext, build_search_pipeline
from .application.use_cases import ListCuisines, SearchRestaurants
from .adapters.inbound.cli import main
from .adapters.outbound.config import (
    ConfigurationError,
    Settings,
    get_settings,
    load_settings,
)
from .adapters.outbound.csv_writer import CsvRestaurantWriter
from .adapters.outbound.glovo_client import GlovoClient

__all__ = [
    "AddressNotFoundError",
    "ConfigurationError",
    "CsvRestaurantWriter",
    "CuisineNotFoundError",
    "GlovoClient",
    "GlovoError",
    "ListCuisines",
    "Pipeline",
    "PipelineStep",
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
