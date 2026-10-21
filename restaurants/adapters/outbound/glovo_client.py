"""Outbound adapter for Glovo's web endpoints.

This module owns request headers, address resolution, pagination, and response
validation. Search orchestration lives in the application layer.
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import replace
from difflib import get_close_matches
from typing import Any

import requests

from ...application.pipeline import Pipeline
from ...domain import Location, Restaurant
from ...domain.errors import (
    AddressNotFoundError,
    CuisineNotFoundError,
    ProviderError,
)
from .config import get_settings
from .glovo_steps import GlovoSearchContext, build_glovo_pipeline
from .settings import Settings


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
        self.location = Location(
            city_code=(
                city_code
                if city_code is not None
                else self.settings.default_city_code
            ),
            city_name=(
                city_name
                if city_name is not None
                else self.settings.default_city_name
            ),
            country_code=(
                country_code
                if country_code is not None
                else self.settings.default_country_code
            ),
            language=(
                language
                if language is not None
                else self.settings.default_language
            ),
            address=address,
        )
        self.timeout = (
            timeout if timeout is not None else self.settings.default_timeout
        )
        self.session = requests.Session()
        self._device_id = str(uuid.uuid4())
        self._session_id = str(uuid.uuid4())
        self._client_id = str(uuid.uuid4())
        self._cuisines: dict[str, tuple[str, str]] | None = None
        self._location_resolved = False
        self._search_pipeline: Pipeline[GlovoSearchContext] = build_glovo_pipeline()

    def _headers(self) -> dict[str, str]:
        settings = self.settings
        location = self.location
        now = str(int(time.time() * 1000))
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": location.language,
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
            "glovo-language-code": location.language,
            "glovo-location-city-code": location.city_code,
            "glovo-location-country-code": location.country_code,
            "glovo-perseus-client-id": self._client_id,
            "glovo-perseus-consent": settings.perseus_consent,
            "glovo-perseus-session-id": self._session_id,
            "glovo-perseus-session-timestamp": now,
            "glovo-request-id": str(uuid.uuid4()),
            "glovo-request-ttl": settings.request_ttl,
            "referer": settings.referer,
            "user-agent": settings.user_agent,
        }
        if location.has_coordinates:
            headers["glovo-delivery-location-latitude"] = str(location.latitude)
            headers["glovo-delivery-location-longitude"] = str(location.longitude)
        return headers

    def _resolve_location(self) -> None:
        location = self.location
        if self._location_resolved or not location.address:
            return

        query = location.address.strip()
        if (
            location.city_name
            and _normalize(location.city_name) not in _normalize(query)
        ):
            query = f"{query}, {location.city_name}"

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
            raise ProviderError(f"Could not look up address '{query}': {exc}") from exc

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

        self.location = replace(
            location,
            latitude=float(match["latitude"]),
            longitude=float(match["longitude"]),
            city_code=(
                str(match["cityCode"]).lower()
                if match.get("cityCode")
                else location.city_code
            ),
            country_code=(
                str(match["countryCode"]).lower()
                if match.get("countryCode")
                else location.country_code
            ),
        )
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
            raise ProviderError(f"Provider request failed: {exc}") from exc

        try:
            data = response.json()["data"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError("Provider returned an unexpected response") from exc

        if not isinstance(data, dict):
            raise ProviderError("Provider returned an unexpected response")
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
                raise ProviderError("Could not load the cuisine list from the provider")
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

    def find_restaurants(self, cuisine: str) -> list[Restaurant]:
        """Return open Glovo restaurants matching ``cuisine``.

        This is the :class:`RestaurantProvider` port implementation. Ranking
        and limiting are application concerns handled by the caller.
        """
        context = GlovoSearchContext(client=self, cuisine=cuisine)
        return self._search_pipeline.run(context).restaurants

    def cuisine_names(self) -> list[str]:
        return sorted(name for name, _ in self.cuisines().values())
