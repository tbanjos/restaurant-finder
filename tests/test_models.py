import unittest

from glovo_restaurants.domain import Restaurant
from glovo_restaurants.domain.helper import (
    parse_distance,
    parse_eta,
    parse_rating,
    parse_votes,
    sort_restaurants,
)


class ParseRatingTests(unittest.TestCase):
    def test_percent(self):
        self.assertEqual(parse_rating("96%"), 96)

    def test_new_and_empty(self):
        self.assertIsNone(parse_rating("New"))
        self.assertIsNone(parse_rating(None))
        self.assertIsNone(parse_rating(""))


class ParseVotesTests(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(parse_votes("(406)"), 406)

    def test_k_suffix(self):
        self.assertEqual(parse_votes("(1k+)"), 1000)
        self.assertEqual(parse_votes("(1.5k+)"), 1500)

    def test_plus_without_k(self):
        self.assertEqual(parse_votes("(500+)"), 500)

    def test_missing(self):
        self.assertEqual(parse_votes(None), 0)
        self.assertEqual(parse_votes(""), 0)


class ParseDistanceTests(unittest.TestCase):
    def test_meters_and_kilometers(self):
        self.assertEqual(parse_distance("<100m"), 100)
        self.assertEqual(parse_distance("1.5km"), 1500)
        self.assertEqual(parse_distance("1,2 km"), 1200)

    def test_missing(self):
        self.assertIsNone(parse_distance(None))
        self.assertIsNone(parse_distance(""))
        self.assertIsNone(parse_distance("nearby"))


class ParseEtaTests(unittest.TestCase):
    def test_range_uses_midpoint(self):
        self.assertEqual(parse_eta("30-40 min"), 35)

    def test_single_value(self):
        self.assertEqual(parse_eta("20 min"), 20)

    def test_hours_and_minutes(self):
        self.assertEqual(parse_eta("1h 10 min"), 70)
        self.assertEqual(parse_eta("1-2 h"), 90)

    def test_missing(self):
        self.assertIsNone(parse_eta(None))
        self.assertIsNone(parse_eta(""))


class RestaurantTests(unittest.TestCase):
    def test_from_api(self):
        entry = {
            "id": "1",
            "title": "Can Pizza",
            "slug": "can-pizza",
            "tag": "Italian",
            "eta": "30-40 min",
            "distance": "<100m",
            "isNew": False,
            "ratings": {"score": "96%", "votes": "(406)"},
            "deliveryFee": {"effectiveFee": "Free"},
        }
        restaurant = Restaurant.from_api(entry)
        self.assertEqual(restaurant.name, "Can Pizza")
        self.assertEqual(restaurant.rating, 96)
        self.assertEqual(restaurant.votes, 406)
        self.assertEqual(restaurant.cuisine, "Italian")
        self.assertEqual(restaurant.delivery_fee, "Free")
        self.assertEqual(restaurant.distance_meters, 100)
        self.assertEqual(restaurant.eta_minutes, 35)
        self.assertEqual(
            restaurant.url,
            "https://glovoapp.com/en/es/barcelona/stores/can-pizza",
        )

    def test_new_store_has_no_rating(self):
        entry = {
            "id": "2",
            "title": "Oak Berry",
            "slug": "oak-berry",
            "ratings": {"score": "New", "votes": ""},
        }
        restaurant = Restaurant.from_api(entry)
        self.assertIsNone(restaurant.rating)
        self.assertTrue(restaurant.is_new)


class SortRestaurantsTests(unittest.TestCase):
    def _restaurant(self, name, rating, votes, distance="", eta=""):
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

    def test_defaults_to_closest_first(self):
        items = [
            self._restaurant("Far", 100, 100, distance="2km"),
            self._restaurant("Near", 80, 1, distance="500m"),
            self._restaurant("Middle", 90, 10, distance="1.2km"),
        ]
        ranked = sort_restaurants(items)
        self.assertEqual([item.name for item in ranked], ["Near", "Middle", "Far"])

    def test_missing_distance_goes_last(self):
        items = [
            self._restaurant("Unknown", 100, 100),
            self._restaurant("Known", 80, 1, distance="1km"),
        ]
        ranked = sort_restaurants(items)
        self.assertEqual([item.name for item in ranked], ["Known", "Unknown"])

    def test_sorted_by_rating_then_votes(self):
        items = [
            self._restaurant("A", 96, 500),
            self._restaurant("B", 100, 10),
            self._restaurant("C", 100, 200),
            self._restaurant("D", 98, 5),
        ]
        ranked = sort_restaurants(items, by="rating")
        self.assertEqual([item.name for item in ranked], ["C", "B", "D", "A"])

    def test_sorted_by_delivery_time(self):
        items = [
            self._restaurant("Slow", 100, 10, eta="45-55 min"),
            self._restaurant("Fast", 80, 1, eta="15-25 min"),
            self._restaurant("Medium", 90, 5, eta="30-40 min"),
        ]
        ranked = sort_restaurants(items, by="delivery-time")
        self.assertEqual([item.name for item in ranked], ["Fast", "Medium", "Slow"])

    def test_unrated_go_last(self):
        items = [
            self._restaurant("New", None, 0),
            self._restaurant("Rated", 90, 3),
        ]
        ranked = sort_restaurants(items, by="rating")
        self.assertEqual([item.name for item in ranked], ["Rated", "New"])

    def test_unknown_sort_option_raises(self):
        with self.assertRaises(ValueError):
            sort_restaurants([], by="price")


if __name__ == "__main__":
    unittest.main()
