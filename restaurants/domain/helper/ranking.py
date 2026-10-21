"""Ranking strategies for restaurant results."""

from __future__ import annotations

from .options import DEFAULT_SORT, SORT_OPTIONS
from ..restaurant import Restaurant


def sort_restaurants(
    restaurants: list[Restaurant], by: str = DEFAULT_SORT
) -> list[Restaurant]:
    """Rank restaurants by the requested strategy.

    ``distance`` (the default) puts the closest restaurants first. ``rating``
    ranks by rating, then votes. ``delivery_time`` ranks by the midpoint of the
    ETA range. Missing values always go last. Names break final ties.
    """
    option = str(by).casefold().replace("-", "_")

    if option in {"distance", "closest"}:
        key = lambda item: (
            item.distance_meters is None,
            item.distance_meters or 0,
            item.rating is None,
            -(item.rating or 0),
            -item.votes,
            item.name.casefold(),
        )
    elif option in {"rating", "ratings"}:
        key = lambda item: (
            item.rating is None,
            -(item.rating or 0),
            -item.votes,
            item.distance_meters is None,
            item.distance_meters or 0,
            item.name.casefold(),
        )
    elif option in {"delivery_time", "delivery", "eta", "time"}:
        key = lambda item: (
            item.eta_minutes is None,
            item.eta_minutes or 0,
            item.distance_meters is None,
            item.distance_meters or 0,
            item.rating is None,
            -(item.rating or 0),
            -item.votes,
            item.name.casefold(),
        )
    else:
        raise ValueError(
            f"Unknown sort option '{by}'. Choose from: {', '.join(SORT_OPTIONS)}"
        )

    return sorted(restaurants, key=key)
