import unittest

from restaurants.application.pipeline import Pipeline
from restaurants.application.cases import ListCuisines, SearchRestaurants
from restaurants.domain import Location, Restaurant


class _Provider:
    location = Location(
        city_code="bcn",
        city_name="barcelona",
        country_code="es",
        language="en",
    )

    def cuisine_names(self):
        return ["Sushi", "Italian"]

    def find_restaurants(self, cuisine):
        return []


class _RestaurantStep:
    name = "fake-restaurants"

    def run(self, context):
        context.restaurants = [
            Restaurant(
                name=context.cuisine,
                rating=None,
                votes=0,
                cuisine="",
                eta="",
                distance="",
                delivery_fee="",
                url="",
            )
        ]


class SearchRestaurantsTests(unittest.TestCase):
    def test_accepts_an_injected_pipeline(self):
        use_case = SearchRestaurants(_Provider(), pipeline=Pipeline((_RestaurantStep(),)))

        restaurants = use_case.execute("italian")

        self.assertEqual([item.name for item in restaurants], ["italian"])

    def test_list_cuisines_sorts_provider_names(self):
        self.assertEqual(ListCuisines(_Provider()).execute(), ["Italian", "Sushi"])


if __name__ == "__main__":
    unittest.main()
