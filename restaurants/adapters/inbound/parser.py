"""Command-line argument parsing for the inbound CLI adapter."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...domain import SORT_OPTIONS
from ..outbound.config import get_settings

def _sort_by(value: str) -> str:
    """Normalize a CLI sort option to its internal name."""
    option = value.casefold().replace("-", "_")
    if option not in SORT_OPTIONS:
        choices = ", ".join(item.replace("_", "-") for item in SORT_OPTIONS)
        raise argparse.ArgumentTypeError(
            f"invalid sort option '{value}' (choose from: {choices})"
        )
    return option

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    settings = get_settings()
    ranking_labels = {
        "distance": "closest",
        "rating": "highest rated",
        "delivery_time": "fastest delivery",
    }
    default_ranking = ranking_labels.get(settings.default_sort, "closest")
    parser = argparse.ArgumentParser(
        prog="restaurant-finder",
        description=(
            "Find open restaurants for a cuisine at a delivery address, "
            f"rank them {default_ranking} first by default, and write the "
            "results to a CSV file."
        ),
    )
    parser.add_argument(
        "-c",
        "--cuisine",
        help='Cuisine to search for, for example "italian", "sushi" or "gluten free".',
    )
    parser.add_argument(
        "-a",
        "--address",
        default=settings.default_address,
        help=(
            "Delivery address used to filter restaurants, for example "
            '"Carrer de Casp 111". Defaults to DELIVERY_ADDRESS, then the city '
            "center."
        ),
    )
    parser.add_argument(
        "--sort-by",
        "--rank-by",
        dest="sort_by",
        type=_sort_by,
        default=settings.default_sort,
        metavar="{distance,rating,delivery-time}",
        help=(
            "Ranking strategy: distance, rating, or delivery-time "
            f"(default: {settings.default_sort.replace('_', '-')})."
        ),
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=settings.default_limit,
        help=(
            "Maximum number of restaurants to write "
            f"(default: {settings.default_limit})."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("restaurants.csv"),
        help="CSV output path (default: restaurants.csv).",
    )
    parser.add_argument(
        "--city",
        default=settings.default_city_name,
        help=f"City to search in (default: {settings.default_city_name}).",
    )
    parser.add_argument(
        "--city-code",
        default=settings.default_city_code,
        help=(
            "Provider city code used by its API "
            f"(default: {settings.default_city_code})."
        ),
    )
    parser.add_argument(
        "--list-cuisines",
        action="store_true",
        help="List available cuisine filters and exit.",
    )
    return parser