import unittest

from glovo_restaurants.models import (
    Restaurant,
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
    def _restaurant(self, name, rating, votes):
        return Restaurant(
            name=name,
            rating=rating,
            votes=votes,
            cuisine="Italian",
            eta="",
            distance="",
            delivery_fee="",
            url="",
        )

    def test_sorted_by_rating_then_votes(self):
        items = [
            self._restaurant("A", 96, 500),
            self._restaurant("B", 100, 10),
            self._restaurant("C", 100, 200),
            self._restaurant("D", 98, 5),
        ]
        ranked = sort_restaurants(items)
        self.assertEqual([item.name for item in ranked], ["C", "B", "D", "A"])

    def test_unrated_go_last(self):
        items = [
            self._restaurant("New", None, 0),
            self._restaurant("Rated", 90, 3),
        ]
        ranked = sort_restaurants(items)
        self.assertEqual([item.name for item in ranked], ["Rated", "New"])


if __name__ == "__main__":
    unittest.main()
