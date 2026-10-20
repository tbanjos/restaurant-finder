# Glovo Restaurant Finder

Find open restaurants on [Glovo](https://glovoapp.com/en/es/barcelona) for a
given cuisine and delivery address, rank them closest first by default (or by
rating or delivery time), and write the results to a CSV file.

By default the script:

1. Uses Barcelona as the city and the city center as the delivery location.
2. Loads the list of food types Glovo exposes for that city.
3. Finds the food type matching the requested cuisine.
4. Fetches every open restaurant in that food type, sorted by rating.
5. Re-ranks them closest first (or by rating/delivery time).
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

# Restaurants near a specific delivery address, closest first
python -m glovo_restaurants --cuisine italian --address "Carrer de Casp 111"

# Rank by rating instead
python -m glovo_restaurants --cuisine italian --sort-by rating

# Rank by fastest delivery estimate
python -m glovo_restaurants --cuisine italian --sort-by delivery-time

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

Results are ranked closest first by default. Use `--sort-by rating` or
`--sort-by delivery-time` (also accepted as `--rank-by`) to change the ranking.
Delivery time uses the midpoint of Glovo's ETA range.

## Configuration

API endpoints, client identity, pagination, and CLI defaults live in
[`glovo_restaurants/config.properties`](glovo_restaurants/config.properties).
The root-level `config.properties` is a symlink to that file for convenience.

To override the configuration without editing the package, set `GLOVO_CONFIG`:

```bash
GLOVO_CONFIG=/etc/glovo-restaurants/config.properties python -m glovo_restaurants --cuisine italian
```

A `config.properties` in the current working directory also takes precedence
over the packaged file. The file uses simple `key=value` lines; `#` and `!`
start comments. Important keys include:

| Key | Purpose |
| --- | --- |
| `api.store_wall_url` | Restaurant listing endpoint |
| `api.address_lookup_url` | Address resolution endpoint |
| `api.app_version`, `api.api_version` | Glovo web-client version pins |
| `api.client_info`, `api.user_agent` | Web-client identity headers |
| `api.page_size` | Stores requested per page |
| `defaults.city_name`, `defaults.city_code` | Default CLI city |
| `defaults.timeout` | HTTP timeout in seconds |
| `defaults.limit` | Default CSV row limit |
| `defaults.sort` | Default ranking (`distance`, `rating`, or `delivery_time`) |

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

## Architecture

The code uses a hexagonal (ports and adapters) architecture. `GlovoClient` is
an outbound adapter that handles HTTP and pagination; the application use cases
drive the composable stages in `glovo_restaurants/application/search.py`, which
resolve the cuisine, fetch entries, keep open stores, map them to `Restaurant`
objects, rank them, and apply the limit. New behaviour should normally be added
as a pipeline stage or a use case, not in an adapter.

See [docs/architecture.md](docs/architecture.md) for the module map, stage
reference, extension guide, API assumptions, troubleshooting, and maintenance
checklist.

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
