import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from glovo_restaurants.client import GlovoClient
from glovo_restaurants.config import (
    ConfigurationError,
    Settings,
    load_settings,
    parse_properties,
)

BASE_PROPERTIES = {
    "api.store_wall_url": "https://example.test/store-wall",
    "api.address_lookup_url": "https://example.test/address",
    "api.app_version": "v9.9.9",
    "api.api_version": "99",
    "api.client_info": "test-client",
    "api.page_size": "25",
    "api.request_ttl": "1234",
    "api.referer": "https://example.test/",
    "api.user_agent": "test-agent",
    "api.app_context": "test",
    "api.app_development_state": "test",
    "api.app_platform": "test",
    "api.app_type": "test",
    "api.perseus_consent": "test",
    "defaults.city_code": "tst",
    "defaults.city_name": "testville",
    "defaults.country_code": "xx",
    "defaults.language": "xx",
    "defaults.timeout": "5.5",
    "defaults.limit": "7",
    "defaults.sort": "rating",
}


def _properties_text(values=None):
    merged = dict(BASE_PROPERTIES)
    merged.update(values or {})
    return "\n".join(f"{key}={value}" for key, value in merged.items())


class ParsePropertiesTests(unittest.TestCase):
    def test_comments_blank_lines_and_separators(self):
        text = """
        # comment
        ! another comment

        alpha=one
        beta: two
        gamma = three
        """

        values = parse_properties(text)

        self.assertEqual(
            values,
            {"alpha": "one", "beta": "two", "gamma": "three"},
        )

    def test_invalid_line_raises(self):
        with self.assertRaises(ConfigurationError):
            parse_properties("missing-separator")


class LoadSettingsTests(unittest.TestCase):
    def _load(self, values=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.properties"
            path.write_text(_properties_text(values), encoding="utf-8")
            return load_settings(path)

    def test_loads_and_converts_values(self):
        settings = self._load()

        self.assertIsInstance(settings, Settings)
        self.assertEqual(settings.store_wall_url, "https://example.test/store-wall")
        self.assertEqual(settings.page_size, 25)
        self.assertEqual(settings.default_timeout, 5.5)
        self.assertEqual(settings.default_limit, 7)
        self.assertEqual(settings.default_sort, "rating")
        self.assertEqual(settings.default_city_code, "tst")

    def test_hyphenated_sort_is_normalized(self):
        settings = self._load({"defaults.sort": "delivery-time"})

        self.assertEqual(settings.default_sort, "delivery_time")

    def test_missing_property_raises(self):
        properties = dict(BASE_PROPERTIES)
        del properties["api.store_wall_url"]

        with self.assertRaises(ConfigurationError):
            Settings.from_properties(properties, source="test")

    def test_invalid_page_size_raises(self):
        with self.assertRaises(ConfigurationError):
            Settings.from_properties(
                {**BASE_PROPERTIES, "api.page_size": "many"}, source="test"
            )

    def test_invalid_sort_raises(self):
        with self.assertRaises(ConfigurationError):
            Settings.from_properties(
                {**BASE_PROPERTIES, "defaults.sort": "price"}, source="test"
            )

    def test_glovo_config_environment_override(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "custom.properties"
            path.write_text(_properties_text(), encoding="utf-8")
            with patch.dict(os.environ, {"GLOVO_CONFIG": str(path)}):
                settings = load_settings()

        self.assertEqual(settings.source, path)
        self.assertEqual(settings.default_city_name, "testville")

    def test_packaged_configuration_is_valid(self):
        path = (
            Path(__file__).resolve().parent.parent
            / "glovo_restaurants"
            / "config.properties"
        )

        settings = load_settings(path)

        self.assertEqual(
            settings.store_wall_url,
            "https://api.glovoapp.com/v1/web/store_wall/category/1",
        )
        self.assertGreater(settings.page_size, 0)


class ClientSettingsTests(unittest.TestCase):
    def test_client_uses_configured_defaults_and_headers(self):
        settings = Settings.from_properties(BASE_PROPERTIES, source="test")
        client = GlovoClient(settings=settings)

        headers = client._headers()

        self.assertEqual(client.settings.store_wall_url, "https://example.test/store-wall")
        self.assertEqual(client.city_code, "tst")
        self.assertEqual(client.city_name, "testville")
        self.assertEqual(client.country_code, "xx")
        self.assertEqual(client.language, "xx")
        self.assertEqual(client.timeout, 5.5)
        self.assertEqual(headers["glovo-app-version"], "v9.9.9")
        self.assertEqual(headers["glovo-api-version"], "99")
        self.assertEqual(headers["glovo-client-info"], "test-client")
        self.assertEqual(headers["glovo-request-ttl"], "1234")
        self.assertEqual(headers["user-agent"], "test-agent")


if __name__ == "__main__":
    unittest.main()
