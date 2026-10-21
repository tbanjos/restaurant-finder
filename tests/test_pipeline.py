import unittest

from restaurants.application.pipeline import Pipeline
from restaurants.application.search import build_search_pipeline
from restaurants.application.search_context import SearchContext
from restaurants.domain import Location, Restaurant


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


class _FakeProvider:
    location = Location(
        city_code="bcn",
        city_name="barcelona",
        country_code="es",
        language="en",
    )

    def __init__(self, restaurants):
        self.restaurants = restaurants
        self.cuisines = []

    def find_restaurants(self, cuisine):
        self.cuisines.append(cuisine)
        return self.restaurants


def _restaurant(name, rating, votes, distance="", eta=""):
    return Restaurant(
        name=name,
        rating=rating,
        votes=votes,
        cuisine="Italian",
        eta=eta,
        distance=distance,
        delivery_fee="",
        url="",
    )


class SearchPipelineTests(unittest.TestCase):
    def test_default_pipeline_fetches_ranks_closest_and_limits(self):
        provider = _FakeProvider(
            [
                _restaurant("Alpha", 100, 10, distance="2km"),
                _restaurant("Beta", 99, 50, distance="500m"),
            ]
        )
        context = SearchContext(client=provider, cuisine="italian", limit=1)

        result = build_search_pipeline().run(context)

        self.assertEqual([item.name for item in result.restaurants], ["Beta"])
        self.assertEqual(provider.cuisines, ["italian"])

    def test_pipeline_can_rank_by_delivery_time(self):
        provider = _FakeProvider(
            [
                _restaurant("Slow", 100, 100, eta="45-55 min"),
                _restaurant("Fast", 80, 10, eta="15-25 min"),
            ]
        )
        context = SearchContext(
            client=provider, cuisine="italian", limit=None, sort_by="delivery_time"
        )

        result = build_search_pipeline().run(context)

        self.assertEqual([item.name for item in result.restaurants], ["Fast", "Slow"])


if __name__ == "__main__":
    unittest.main()
