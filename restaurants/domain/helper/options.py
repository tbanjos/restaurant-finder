"""Supported restaurant ranking options."""

from __future__ import annotations

SORT_DISTANCE = "distance"
SORT_RATING = "rating"
SORT_DELIVERY_TIME = "delivery_time"

SORT_OPTIONS = (SORT_DISTANCE, SORT_RATING, SORT_DELIVERY_TIME)
DEFAULT_SORT = SORT_DISTANCE
