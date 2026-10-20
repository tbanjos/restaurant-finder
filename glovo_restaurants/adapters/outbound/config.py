"""Typed configuration loaded from a Java-style properties file.

The packaged ``config.properties`` is the default source. Resolution order is:

1. ``GLOVO_CONFIG`` environment variable, when set.
2. ``config.properties`` in the current working directory.
3. ``config.properties`` next to the project root (source checkouts).
4. ``config.properties`` packaged with :mod:`glovo_restaurants`.

Keeping configuration out of the client makes API-version bumps and deployment
overrides possible without editing Python code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping

from ...domain import SORT_OPTIONS


class ConfigurationError(RuntimeError):
    """Raised when the properties file is missing or invalid."""


def _config_candidates() -> list[Path]:
    package_root = Path(__file__).resolve().parents[2]
    project_root = package_root.parent
    return [
        project_root / "config.properties",
        package_root / "config.properties",
    ]


def default_config_path() -> Path:
    """Return the properties file that will be loaded by default."""
    override = os.environ.get("GLOVO_CONFIG")
    if override:
        path = Path(override).expanduser()
        if not path.is_file():
            raise ConfigurationError(f"GLOVO_CONFIG does not exist: {path}")
        return path

    cwd_file = Path.cwd() / "config.properties"
    if cwd_file.is_file():
        return cwd_file

    for candidate in _config_candidates():
        if candidate.is_file():
            return candidate

    raise ConfigurationError(
        "Could not find config.properties. Set GLOVO_CONFIG to its location."
    )


def parse_properties(text: str, *, source: str = "<properties>") -> dict[str, str]:
    """Parse ``key=value`` / ``key: value`` lines, ignoring blank lines."""
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(("#", "!")):
            continue

        separator = "=" if "=" in line else ":" if ":" in line else None
        if separator is None:
            raise ConfigurationError(
                f"{source}:{line_number}: expected key=value, got {raw_line!r}"
            )

        key, value = line.split(separator, 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ConfigurationError(
                f"{source}:{line_number}: property name is empty"
            )
        values[key] = value
    return values


def _require(properties: Mapping[str, str], key: str, *, source: str) -> str:
    try:
        return properties[key]
    except KeyError as exc:
        raise ConfigurationError(f"{source}: missing required property '{key}'") from exc


def _as_int(value: str, key: str, *, source: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigurationError(
            f"{source}: property '{key}' must be an integer, got {value!r}"
        ) from exc


def _as_float(value: str, key: str, *, source: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ConfigurationError(
            f"{source}: property '{key}' must be a number, got {value!r}"
        ) from exc


@dataclass(frozen=True)
class Settings:
    """Application settings with parsed and validated values."""

    store_wall_url: str
    address_lookup_url: str
    app_version: str
    api_version: str
    client_info: str
    page_size: int
    request_ttl: str
    referer: str
    user_agent: str
    app_context: str
    app_development_state: str
    app_platform: str
    app_type: str
    perseus_consent: str
    default_city_code: str
    default_city_name: str
    default_country_code: str
    default_language: str
    default_timeout: float
    default_limit: int
    default_sort: str
    source: Path | None = None

    @classmethod
    def from_properties(
        cls, properties: Mapping[str, str], *, source: Path | str | None = None
    ) -> "Settings":
        """Build settings from a mapping, validating required values."""
        label = str(source or "<properties>")

        def required(key: str) -> str:
            return _require(properties, key, source=label)

        page_size = _as_int(required("api.page_size"), "api.page_size", source=label)
        if page_size < 1:
            raise ConfigurationError(
                f"{label}: property 'api.page_size' must be at least 1"
            )

        default_timeout = _as_float(
            required("defaults.timeout"), "defaults.timeout", source=label
        )
        if default_timeout <= 0:
            raise ConfigurationError(
                f"{label}: property 'defaults.timeout' must be greater than 0"
            )

        default_limit = _as_int(
            required("defaults.limit"), "defaults.limit", source=label
        )
        if default_limit < 1:
            raise ConfigurationError(
                f"{label}: property 'defaults.limit' must be at least 1"
            )

        default_sort = required("defaults.sort").casefold().replace("-", "_")
        if default_sort not in SORT_OPTIONS:
            raise ConfigurationError(
                f"{label}: property 'defaults.sort' must be one of "
                f"{', '.join(SORT_OPTIONS)}"
            )

        return cls(
            store_wall_url=required("api.store_wall_url"),
            address_lookup_url=required("api.address_lookup_url"),
            app_version=required("api.app_version"),
            api_version=required("api.api_version"),
            client_info=required("api.client_info"),
            page_size=page_size,
            request_ttl=required("api.request_ttl"),
            referer=required("api.referer"),
            user_agent=required("api.user_agent"),
            app_context=required("api.app_context"),
            app_development_state=required("api.app_development_state"),
            app_platform=required("api.app_platform"),
            app_type=required("api.app_type"),
            perseus_consent=required("api.perseus_consent"),
            default_city_code=required("defaults.city_code"),
            default_city_name=required("defaults.city_name"),
            default_country_code=required("defaults.country_code"),
            default_language=required("defaults.language"),
            default_timeout=default_timeout,
            default_limit=default_limit,
            default_sort=default_sort,
            source=Path(source) if source is not None else None,
        )


def load_settings(path: str | Path | None = None) -> Settings:
    """Load settings from ``path`` or the default properties file."""
    config_path = Path(path).expanduser() if path is not None else default_config_path()
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(
            f"Could not read configuration file {config_path}: {exc}"
        ) from exc
    return Settings.from_properties(
        parse_properties(text, source=str(config_path)),
        source=config_path,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide default settings."""
    return load_settings()
