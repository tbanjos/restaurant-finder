import unittest

from glovo_restaurants.adapters.outbound.glovo_steps import (
    restaurant_from_api,
    store_is_open,
)
from glovo_restaurants.domain import Location

LOCATION = Location(
    city_code="bcn",
    city_name="barcelona",
    country_code="es",
    language="en",
)


class RestaurantMappingTests(unittest.TestCase):
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
        restaurant = restaurant_from_api(entry, LOCATION)
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
        restaurant = restaurant_from_api(entry, LOCATION)
        self.assertIsNone(restaurant.rating)
        self.assertTrue(restaurant.is_new)


class StoreAvailabilityTests(unittest.TestCase):
    def test_store_is_open_treats_missing_availability_as_open(self):
        self.assertTrue(store_is_open({}))
        self.assertTrue(store_is_open({"availability": {"status": "open"}}))
        self.assertFalse(store_is_open({"availability": {"status": "CLOSED"}}))


if __name__ == "__main__":
    unittest.main()
