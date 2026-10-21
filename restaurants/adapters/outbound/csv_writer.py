"""Outbound adapter that writes ranked restaurants to a CSV file."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from ...domain import Restaurant

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


class CsvRestaurantWriter:
    """Write restaurants to a UTF-8 CSV file with a BOM."""

    def __init__(self, output: Path) -> None:
        self.output = output

    def write(self, restaurants: Sequence[Restaurant]) -> None:
        with self.output.open("w", encoding="utf-8-sig", newline="") as handle:
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

def _rating_value(rating: float | None) -> str | int:
    if rating is None:
        return ""
    return int(rating) if rating.is_integer() else rating
