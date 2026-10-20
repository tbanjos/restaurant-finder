import unittest

from glovo_restaurants.application.pipeline import Pipeline
from glovo_restaurants.application.cases import ListCuisines, SearchRestaurants
from glovo_restaurants.domain import Restaurant


class _Provider:
    city_name = "barcelona"
    country_code = "es"
    language = "en"

    def resolve_cuisine(self, query):
        return ("Italian", "34685")

    def cuisines(self):
        return {"italian": ("Italian", "34685"), "sushi": ("Sushi", "123")}

    def fetch_store_entries(self, filters):
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
