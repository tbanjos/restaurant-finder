"""Inbound HTTP-free CLI adapter for restaurant searches."""

from __future__ import annotations

import sys

from ...application.cases import ListCuisines, SearchRestaurants
from ...domain.errors import CuisineNotFoundError, ProviderError
from ..outbound.configuration_error import ConfigurationError
from ..outbound.csv_writer import CsvRestaurantWriter
from ..outbound.provider import build_provider
from .parser import build_parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    try:
        parser = build_parser()
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    args = parser.parse_args(argv)

    if not args.list_cuisines and not args.cuisine:
        parser.error("--cuisine is required unless --list-cuisines is used")
    if args.limit < 1:
        parser.error("--limit must be at least 1")

    try:
        client = build_provider(
            city_code=args.city_code,
            city_name=args.city,
            address=args.address,
        )
        if args.list_cuisines:
            for name in ListCuisines(client).execute():
                print(name)
            return 0

        print(f"Fetching {args.cuisine!r} restaurants...", file=sys.stderr)
        restaurants = SearchRestaurants(client).execute(
            args.cuisine,
            limit=args.limit,
            sort_by=args.sort_by,
        )
        if not restaurants:
            print("No restaurants found.", file=sys.stderr)
            return 1

        args.output.parent.mkdir(parents=True, exist_ok=True)
        CsvRestaurantWriter(args.output).write(restaurants)
    except CuisineNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except ProviderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Wrote {len(restaurants)} restaurants to {args.output}",
        file=sys.stderr,
    )
    return 0
