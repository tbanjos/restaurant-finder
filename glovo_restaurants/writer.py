from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .models import SORT_OPTIONS, Restaurant

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


def write_csv(restaurants: list[Restaurant], output: Path) -> None:
    """Write ``restaurants`` to ``output`` as a UTF-8 CSV with a BOM."""
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

def _rating_value(rating: float | None) -> str | int:
    if rating is None:
        return ""
    return int(rating) if rating.is_integer() else rating