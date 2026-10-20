from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .client import CuisineNotFoundError, GlovoClient, GlovoError
from .models import Restaurant

FIELDS = [
    "name",
    "rating_percent",
    "votes",
    "cuisine",
    "eta",
    "distance",
    "delivery_fee",
    "url",
]


def _rating_value(rating: float | None) -> str | int:
    if rating is None:
        return ""
    return int(rating) if rating.is_integer() else rating


def write_csv(restaurants: list[Restaurant], output: Path) -> None:
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for restaurant in restaurants:
            writer.writerow(
                {
                    "name": restaurant.name,
                    "rating_percent": _rating_value(restaurant.rating),
                    "votes": restaurant.votes,
                    "cuisine": restaurant.cuisine,
                    "eta": restaurant.eta,
                    "distance": restaurant.distance,
                    "delivery_fee": restaurant.delivery_fee,
                    "url": restaurant.url,
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glovo-restaurants",
        description=(
            "Find open Glovo restaurants for a cuisine at a delivery address, "
            "rank them by rating, and write the results to a CSV file."
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
        default=None,
        help=(
            "Delivery address used to filter restaurants, for example "
            '"Carrer de Casp 111". Defaults to the city center.'
        ),
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=30,
        help="Maximum number of restaurants to write (default: 30).",
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
        default="barcelona",
        help="City to search in (default: barcelona).",
    )
    parser.add_argument(
        "--city-code",
        default="bcn",
        help="Glovo city code used by its API (default: bcn).",
    )
    parser.add_argument(
        "--list-cuisines",
        action="store_true",
        help="List available cuisine filters and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.list_cuisines and not args.cuisine:
        parser.error("--cuisine is required unless --list-cuisines is used")
    if args.limit < 1:
        parser.error("--limit must be at least 1")

    client = GlovoClient(
        city_code=args.city_code,
        city_name=args.city,
        address=args.address,
    )
    try:
        if args.list_cuisines:
            for name in client.cuisine_names():
                print(name)
            return 0

        print(f"Fetching {args.cuisine!r} restaurants from Glovo...", file=sys.stderr)
        restaurants = client.fetch_restaurants(args.cuisine, limit=args.limit)
        if not restaurants:
            print("No restaurants found.", file=sys.stderr)
            return 1

        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_csv(restaurants, args.output)
    except CuisineNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except GlovoError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Wrote {len(restaurants)} restaurants to {args.output}",
        file=sys.stderr,
    )
    return 0
