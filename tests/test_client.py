import unittest

from glovo_restaurants.adapters.outbound.glovo_client import GlovoClient
from glovo_restaurants.domain.errors import GlovoError


def _entry(store_id, title, score, votes, status="OPEN"):
    return {
        "id": str(store_id),
        "title": title,
        "slug": title.lower().replace(" ", "-"),
        "tag": "Italian",
        "ratings": {"score": score, "votes": votes},
        "deliveryFee": {"effectiveFee": "Free"},
        "availability": {"status": status},
    }


class FakeClient(GlovoClient):
    def __init__(self, pages):
        super().__init__()
        self._pages = pages
        self.calls = []

    def resolve_cuisine(self, query):
        return ("Italian", "34685")

    def _post(self, **kwargs):
        self.calls.append(kwargs)
        index = len(self.calls) - 1
        batch = self._pages[index] if index < len(self._pages) else []
        return {"stores": {"entries": batch, "pagination": {"totalEntries": 0}}}


class FetchRestaurantsTests(unittest.TestCase):
    def test_paginates_dedupes_and_limits(self):
        pages = [
            [
                _entry(1, "Alpha", "100%", "(10)"),
                _entry(2, "Beta", "99%", "(50)"),
            ],
            [
                _entry(2, "Beta", "99%", "(50)"),
                _entry(3, "Gamma", "100%", "(5)"),
            ],
            [],
        ]
        client = FakeClient(pages)
        restaurants = client.fetch_restaurants("italian", limit=2)

        self.assertEqual([item.name for item in restaurants], ["Alpha", "Gamma"])
        self.assertEqual(len(client.calls), 3)
        self.assertIsNone(client.calls[0]["previous_store_ids"])
        self.assertEqual(client.calls[1]["previous_store_ids"], ["1", "2"])
        self.assertEqual(client.calls[2]["previous_store_ids"], ["1", "2", "3"])

    def test_filters_out_closed_restaurants(self):
        pages = [
            [
                _entry(1, "Open", "100%", "(10)"),
                _entry(2, "Closed", "99%", "(50)", status="CLOSED"),
                _entry(3, "Also Open", "98%", "(5)"),
            ],
            [],
        ]
        client = FakeClient(pages)
        restaurants = client.fetch_restaurants("italian", limit=None)

        self.assertEqual([item.name for item in restaurants], ["Open", "Also Open"])


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self._payload = payload
        self.get_calls = []

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return _FakeResponse(self._payload)


class AddressLookupTests(unittest.TestCase):
    def test_resolves_address_and_sets_location_headers(self):
        client = GlovoClient(address="Carrer de Casp 111", city_name="barcelona")
        client.session = _FakeSession(
            {
                "addresses": [
                    {"title": "No coordinates"},
                    {
                        "title": "Carrer de Casp, 111",
                        "latitude": 41.3961889,
                        "longitude": 2.1796525,
                        "cityCode": "BCN",
                        "countryCode": "ES",
                    },
                ]
            }
        )

        client._resolve_location()

        headers = client._headers()
        self.assertEqual(headers["glovo-delivery-location-latitude"], "41.3961889")
        self.assertEqual(headers["glovo-delivery-location-longitude"], "2.1796525")
        self.assertEqual(headers["glovo-location-city-code"], "bcn")
        self.assertEqual(client.location.city_code, "bcn")
        self.assertEqual(client.location.latitude, 41.3961889)
        self.assertEqual(client.location.longitude, 2.1796525)
        self.assertTrue(client.location.has_coordinates)
        self.assertIn("Carrer de Casp 111, barcelona", client.session.get_calls[0][1]["params"]["address"])

    def test_missing_address_raises(self):
        client = GlovoClient(address="Nowhere")
        client.session = _FakeSession({"addresses": []})

        with self.assertRaises(GlovoError):
            client._resolve_location()

    def test_no_address_keeps_default_location(self):
        client = GlovoClient()
        client.session = _FakeSession({})

        client._resolve_location()

        self.assertNotIn("glovo-delivery-location-latitude", client._headers())


if __name__ == "__main__":
    unittest.main()
