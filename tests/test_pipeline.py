import unittest

from glovo_restaurants.application.pipeline import Pipeline
from glovo_restaurants.domain import Location
from glovo_restaurants.application.search import build_search_pipeline
from glovo_restaurants.application.search_context import SearchContext
from glovo_restaurants.application.steps import store_is_open


class _Step:
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    def run(self, context):
        self.calls.append(self.name)
        context.setdefault("trace", []).append(self.name)


class PipelineTests(unittest.TestCase):
    def test_runs_steps_in_order_and_returns_context(self):
        calls = []
        pipe = Pipeline((_Step("first", calls), _Step("second", calls)))
        context = {}

        result = pipe.run(context)

        self.assertIs(result, context)
        self.assertEqual(calls, ["first", "second"])

    def test_exposes_steps(self):
        calls = []
        pipe = Pipeline((_Step("first", calls), _Step("second", calls)))

        self.assertEqual(len(pipe), 2)
        self.assertEqual([step.name for step in pipe], ["first", "second"])


class _FakeClient:
    location = Location(
        city_code="bcn",
        city_name="barcelona",
        country_code="es",
        language="en",
    )

    def __init__(self, entries):
        self.entries = entries

    def resolve_cuisine(self, query):
        return ("Italian", "34685")

    def fetch_store_entries(self, filters):
        self.filters = filters
        return self.entries


class SearchPipelineTests(unittest.TestCase):
    def _entry(
        self, store_id, title, score, votes, status="OPEN", distance="", eta=""
    ):
        return {
            "id": store_id,
            "title": title,
            "slug": title.lower().replace(" ", "-"),
            "tag": "Italian",
            "ratings": {"score": score, "votes": votes},
            "availability": {"status": status},
            "distance": distance,
            "eta": eta,
        }

    def test_default_pipeline_filters_ranks_closest_and_limits(self):
        client = _FakeClient(
            [
                self._entry(
                    "1", "Closed", "100%", "(100)", status="CLOSED", distance="50m"
                ),
                self._entry("2", "Alpha", "100%", "(10)", distance="2km"),
                self._entry("3", "Beta", "99%", "(50)", distance="500m"),
            ]
        )
        context = SearchContext(client=client, cuisine="italian", limit=1)

        result = build_search_pipeline().run(context)

        self.assertEqual([item.name for item in result.restaurants], ["Beta"])
        self.assertEqual(
            result.filters,
            [
                {"filterId": "ADMIN_FILTERS", "filterAttributeIds": ["34685"]},
                {"filterId": "SORT_BY", "filterAttributeIds": ["RATING"]},
            ],
        )

    def test_pipeline_can_rank_by_delivery_time(self):
        client = _FakeClient(
            [
                self._entry("1", "Slow", "100%", "(100)", eta="45-55 min"),
                self._entry("2", "Fast", "80%", "(10)", eta="15-25 min"),
            ]
        )
        context = SearchContext(
            client=client, cuisine="italian", limit=None, sort_by="delivery_time"
        )

        result = build_search_pipeline().run(context)

        self.assertEqual([item.name for item in result.restaurants], ["Fast", "Slow"])

    def test_store_is_open_treats_missing_availability_as_open(self):
        self.assertTrue(store_is_open({}))
        self.assertTrue(store_is_open({"availability": {"status": "open"}}))
        self.assertFalse(store_is_open({"availability": {"status": "CLOSED"}}))


if __name__ == "__main__":
    unittest.main()
