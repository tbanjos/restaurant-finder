"""Outbound adapter for Glovo's web endpoints.

This module owns request headers, address resolution, pagination, and response
validation. Search orchestration lives in the application layer.
"""

from __future__ import annotations

import re
import time
import uuid
from difflib import get_close_matches
from typing import Any

import requests

from ...application.use_cases import SearchRestaurants
from ...domain.errors import (
    AddressNotFoundError,
    CuisineNotFoundError,
    GlovoError,
)
from ...domain import Restaurant
from .config import Settings, get_settings


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


class GlovoClient:
    def __init__(
        self,
        *,
        city_code: str | None = None,
        city_name: str | None = None,
        country_code: str | None = None,
        language: str | None = None,
        address: str | None = None,
        timeout: float | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.city_code = (
            city_code if city_code is not None else self.settings.default_city_code
        )
        self.city_name = (
            city_name if city_name is not None else self.settings.default_city_name
        )
        self.country_code = (
            country_code
            if country_code is not None
            else self.settings.default_country_code
        )
        self.language = (
            language if language is not None else self.settings.default_language
        )
        self.address = address
        self.latitude: float | None = None
        self.longitude: float | None = None
        self.timeout = (
            timeout if timeout is not None else self.settings.default_timeout
        )
        self.session = requests.Session()
        self._device_id = str(uuid.uuid4())
        self._session_id = str(uuid.uuid4())
        self._client_id = str(uuid.uuid4())
        self._cuisines: dict[str, tuple[str, str]] | None = None
        self._location_resolved = False

    def _headers(self) -> dict[str, str]:
        settings = self.settings
        now = str(int(time.time() * 1000))
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": self.language,
            "content-type": "application/json",
            "glovo-api-version": settings.api_version,
            "glovo-app-context": settings.app_context,
            "glovo-app-development-state": settings.app_development_state,
            "glovo-app-platform": settings.app_platform,
            "glovo-app-type": settings.app_type,
            "glovo-app-version": settings.app_version,
            "glovo-client-info": settings.client_info,
            "glovo-delivery-location-accuracy": "0",
            "glovo-delivery-location-timestamp": now,
            "glovo-device-urn": f"glv:device:{self._device_id}",
            "glovo-dynamic-session-id": self._session_id,
            "glovo-language-code": self.language,
            "glovo-location-city-code": self.city_code,
            "glovo-location-country-code": self.country_code,
            "glovo-perseus-client-id": self._client_id,
            "glovo-perseus-consent": settings.perseus_consent,
            "glovo-perseus-session-id": self._session_id,
            "glovo-perseus-session-timestamp": now,
            "glovo-request-id": str(uuid.uuid4()),
            "glovo-request-ttl": settings.request_ttl,
            "referer": settings.referer,
            "user-agent": settings.user_agent,
        }
        if self.latitude is not None and self.longitude is not None:
            headers["glovo-delivery-location-latitude"] = str(self.latitude)
            headers["glovo-delivery-location-longitude"] = str(self.longitude)
        return headers

    def _resolve_location(self) -> None:
        if self._location_resolved or not self.address:
            return

        query = self.address.strip()
        if self.city_name and _normalize(self.city_name) not in _normalize(query):
            query = f"{query}, {self.city_name}"

        try:
            response = self.session.get(
                self.settings.address_lookup_url,
                params={"address": query, "allowFallback": "true"},
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            addresses = response.json().get("addresses") or []
        except (requests.RequestException, ValueError, AttributeError) as exc:
            raise GlovoError(f"Could not look up address '{query}': {exc}") from exc

        match = next(
            (
                item
                for item in addresses
                if item.get("latitude") is not None and item.get("longitude") is not None
            ),
            None,
        )
        if match is None:
            raise AddressNotFoundError(
                f"Could not find address '{query}'. Try adding more detail."
            )

        self.latitude = float(match["latitude"])
        self.longitude = float(match["longitude"])
        if match.get("cityCode"):
            self.city_code = str(match["cityCode"]).lower()
        if match.get("countryCode"):
            self.country_code = str(match["countryCode"]).lower()
        self._location_resolved = True

    def _post(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
        filters: list[dict[str, Any]] | None = None,
        previous_store_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        self._resolve_location()

        body: dict[str, Any] = {"filters": filters or []}
        if previous_store_ids:
            body["previousStoreIds"] = previous_store_ids

        try:
            response = self.session.post(
                self.settings.store_wall_url,
                params={
                    "moduleId": "StoreFeeds",
                    "offset": offset,
                    "limit": (
                        self.settings.page_size if limit is None else limit
                    ),
                    "handlingType": "DELIVERY",
                },
                headers=self._headers(),
                json=body,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise GlovoError(f"Glovo request failed: {exc}") from exc

        try:
            data = response.json()["data"]
        except (ValueError, KeyError, TypeError) as exc:
            raise GlovoError("Glovo returned an unexpected response") from exc

        if not isinstance(data, dict):
            raise GlovoError("Glovo returned an unexpected response")
        return data

    def cuisines(self) -> dict[str, tuple[str, str]]:
        """Return ``{normalized_name: (display_name, filter_id)}``."""
        if self._cuisines is None:
            data = self._post(limit=1)
            cuisines: dict[str, tuple[str, str]] = {}
            for item in data.get("filters") or []:
                if item.get("filterId") != "ADMIN_FILTERS":
                    continue
                name = item.get("filterAttributeTitle") or ""
                filter_id = item.get("filterAttributeId")
                if name and filter_id:
                    cuisines[_normalize(name)] = (name, str(filter_id))
            if not cuisines:
                raise GlovoError("Could not load the cuisine list from Glovo")
            self._cuisines = cuisines
        return self._cuisines

    def resolve_cuisine(self, query: str) -> tuple[str, str]:
        cuisines = self.cuisines()
        key = _normalize(query)
        if key in cuisines:
            return cuisines[key]

        suggestions = get_close_matches(key, list(cuisines), n=5, cutoff=0.6)
        if suggestions:
            names = ", ".join(cuisines[item][0] for item in suggestions)
            raise CuisineNotFoundError(
                f"Unknown cuisine '{query}'. Did you mean: {names}?"
            )
        raise CuisineNotFoundError(
            f"Unknown cuisine '{query}'. Use --list-cuisines to see the options."
        )

    def fetch_store_entries(
        self, filters: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Fetch every store entry matching ``filters``.

        Glovo paginates the store wall and may repeat entries between pages, so
        this method deduplicates by store id. Availability filtering belongs to
        the search pipeline, not to this transport-level helper.
        """
        entries: list[dict[str, Any]] = []
        seen: set[str] = set()
        seen_order: list[str] = []
        offset = 0

        while True:
            data = self._post(
                offset=offset,
                limit=self.settings.page_size,
                filters=filters,
                previous_store_ids=list(seen_order) or None,
            )
            stores = data.get("stores") or {}
            batch = stores.get("entries") or []

            new_entries = [
                entry
                for entry in batch
                if str(entry.get("id")) not in seen
            ]
            if not new_entries:
                break

            for entry in new_entries:
                store_id = str(entry.get("id"))
                seen.add(store_id)
                seen_order.append(store_id)
                entries.append(entry)

            offset += len(batch)

        return entries

    def fetch_restaurants(
        self,
        cuisine: str,
        *,
        limit: int | None = 30,
        sort_by: str | None = None,
    ) -> list[Restaurant]:
        """Return ranked open restaurants for ``cuisine``.

        ``sort_by`` accepts ``distance``, ``rating``, or ``delivery_time``.
        When omitted, the ``defaults.sort`` setting is used. This convenience
        method keeps the historical client API working; new callers should use
        :class:`~glovo_restaurants.application.use_cases.SearchRestaurants`.
        """
        return SearchRestaurants(self).execute(
            cuisine,
            limit=limit,
            sort_by=sort_by or self.settings.default_sort,
        )

    def cuisine_names(self) -> list[str]:
        return sorted(name for name, _ in self.cuisines().values())
