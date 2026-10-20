# Glovo Restaurant Finder

Find open restaurants on [Glovo](https://glovoapp.com/en/es/barcelona) for a
given cuisine and delivery address, rank them by rating, and write the results
to a CSV file.

By default the script:

1. Uses Barcelona as the city and the city center as the delivery location.
2. Loads the list of food types Glovo exposes for that city.
3. Finds the food type matching the requested cuisine.
4. Fetches every open restaurant in that food type, sorted by rating.
5. Re-ranks them by rating (then by number of votes, then by name).
6. Writes the top 30 to a CSV file.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Or install it as a command:

```bash
pip install -e .
```

## Usage

```bash
# Top 30 Italian restaurants in Barcelona -> restaurants.csv
python -m glovo_restaurants --cuisine italian

# Restaurants near a specific delivery address
python -m glovo_restaurants --cuisine italian --address "Carrer de Casp 111"

# A different city (the city code can also be supplied explicitly)
python -m glovo_restaurants --cuisine sushi --city madrid --city-code mad

# Top 30 sushi restaurants -> sushi.csv
python -m glovo_restaurants --cuisine sushi --output sushi.csv

# A cuisine with a space or special characters
python -m glovo_restaurants --cuisine "gluten free" --output gluten_free.csv

# Change how many rows are written
python -m glovo_restaurants --cuisine pizza --limit 50

# Show every cuisine Glovo supports
python -m glovo_restaurants --list-cuisines
```

If installed with `pip install -e .`, the same options work through the
`glovo-restaurants` command.

Cuisine matching ignores case and punctuation, so `Italian`, `italian`, and
`ITALIAN` all work. A close-match suggestion is shown for typos.

When `--address` is omitted the search uses the selected city (Barcelona by
default). When it is supplied, the address is resolved through Glovo's address
lookup and the delivery location is sent with every request. Only restaurants
whose availability status is `OPEN` are included in the output.

## Output

The CSV is UTF-8 with a BOM so it opens correctly in Excel:

| Column | Meaning |
| --- | --- |
| `name` | Restaurant name |
| `rating_percent` | Rating percentage shown by Glovo, empty if unrated |
| `votes` | Number of ratings, `1000` for `(1k+)` |
| `cuisine` | Glovo food-type tag |
| `eta` | Delivery estimate |
| `distance` | Distance shown in the listing |
| `delivery_fee` | Effective delivery fee (`Free`, `0,49 €`, ...) |
| `url` | Link to the store page |

Example:

```csv
name,rating_percent,votes,cuisine,eta,distance,delivery_fee,url
Spaccanapoli Balmes,100,165,Italian,30-40 min,<100m,Free,https://glovoapp.com/en/es/barcelona/stores/spaccanapoli-balmes-barcelona
Chicago's Pizza Factory,100,109,Italian,30-40 min,<100m,Free,https://glovoapp.com/en/es/barcelona/stores/chicagos-pizza-factory-barcelona
```

## Tests

```bash
python -m unittest discover -s tests
```

## Notes

- Data comes from Glovo's public web store-listing and address-lookup endpoints.
  It is not an officially documented API and may change without notice.
- A single run makes a few requests (one per 50 restaurants plus one for the
  cuisine list, and one address lookup if `--address` is used), so it is polite
  to the site. Avoid running it in a tight loop.
- Restaurants are returned for the selected city or delivery address. Some
  stores may still not be available at every address within that area.
