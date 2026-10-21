"""Typed configuration loaded from a Java-style properties file.

The packaged ``config.properties`` is the default source. Resolution order is:

1. ``GLOVO_CONFIG`` environment variable, when set.
2. ``config.properties`` in the current working directory.
3. ``config.properties`` next to the project root (source checkouts).
4. ``config.properties`` packaged with :mod:`restaurants`.

Keeping configuration out of the client makes API-version bumps and deployment
overrides possible without editing Python code.
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

from .configuration_error import ConfigurationError
from .settings import Settings

_ENVIRONMENT_DEFAULTS = {
    "default_address": ("DELIVERY_ADDRESS", "GLOVO_DEFAULT_ADDRESS"),
    "default_city_name": ("DELIVERY_CITY", "GLOVO_DEFAULT_CITY"),
    "default_city_code": ("DELIVERY_CITY_CODE", "GLOVO_DEFAULT_CITY_CODE"),
}


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


def _with_environment_defaults(settings: Settings) -> Settings:
    """Apply address and city defaults from the environment."""
    overrides = {}
    for field, names in _ENVIRONMENT_DEFAULTS.items():
        for name in names:
            value = os.environ.get(name)
            if value is not None and value.strip():
                overrides[field] = value.strip()
                break
    return replace(settings, **overrides) if overrides else settings


def load_settings(path: str | Path | None = None) -> Settings:
    """Load settings from ``path`` or the default properties file."""
    config_path = Path(path).expanduser() if path is not None else default_config_path()
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(
            f"Could not read configuration file {config_path}: {exc}"
        ) from exc
    settings = Settings.from_properties(
        parse_properties(text, source=str(config_path)),
        source=config_path,
    )
    return _with_environment_defaults(settings)


def get_settings() -> Settings:
    """Return the default settings, including environment overrides."""
    return load_settings()
