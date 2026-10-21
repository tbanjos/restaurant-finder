# Restaurant Finder

Find open restaurants for a given cuisine and delivery address, rank them
closest first by default (or by rating or delivery time), and write the results
to a CSV file.

The finder is provider-agnostic: the application depends only on the
`RestaurantProvider` port, and provider details stay in an outbound adapter. The
bundled adapter supports Glovo, so the default configuration and examples use
that provider.

By default the script:

1. Uses Barcelona as the city and the city center as the delivery location.
2. Loads the list of food types the provider exposes for that city.
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
python -m restaurants --cuisine italian

# Restaurants near a specific delivery address, closest first
python -m restaurants --cuisine italian --address "Carrer de Casp 111"

# Rank by rating instead
python -m restaurants --cuisine italian --sort-by rating

# Rank by fastest delivery estimate
python -m restaurants --cuisine italian --sort-by delivery-time

# A different city (the city code can also be supplied explicitly)
python -m restaurants --cuisine sushi --city madrid --city-code mad

# Top 30 sushi restaurants -> sushi.csv
python -m restaurants --cuisine sushi --output sushi.csv

# A cuisine with a space or special characters
python -m restaurants --cuisine "gluten free" --output gluten_free.csv

# Change how many rows are written
python -m restaurants --cuisine pizza --limit 50

# Show every cuisine the provider supports
python -m restaurants --list-cuisines
```

If installed with `pip install -e .`, the same options work through the
`glovo-restaurants` command (kept for backward compatibility).

Cuisine matching ignores case and punctuation, so `Italian`, `italian`, and
`ITALIAN` all work. A close-match suggestion is shown for typos.

When `--address` is omitted the search uses the selected city (Barcelona by
default). When it is supplied, the address is resolved through the provider's
address lookup and the delivery location is sent with every request. Only
restaurants whose availability status is `OPEN` are included in the output.

Results are ranked closest first by default. Use `--sort-by rating` or
`--sort-by delivery-time` (also accepted as `--rank-by`) to change the ranking.
Delivery time uses the midpoint of the provider's ETA range.

## Configuration

API endpoints, client identity, pagination, and CLI defaults live in
[`restaurants/config.properties`](restaurants/config.properties). The bundled
file configures the default provider adapter. The root-level `config.properties`
is a symlink to that file for convenience.

To override the configuration without editing the package, set `GLOVO_CONFIG`:

```bash
GLOVO_CONFIG=/etc/glovo-restaurants/config.properties python -m restaurants --cuisine italian
```

The default delivery address and city can be supplied through the environment,
which keeps repeated commands short:

```bash
DELIVERY_ADDRESS="Carrer de Casp 111" DELIVERY_CITY=madrid DELIVERY_CITY_CODE=mad \
  python -m restaurants --cuisine sushi
```

`DELIVERY_ADDRESS`, `DELIVERY_CITY`, and `DELIVERY_CITY_CODE` override the properties
file. Explicit `--address`, `--city`, and `--city-code` flags still take
precedence.

A `config.properties` in the current working directory also takes precedence
over the packaged file. The file uses simple `key=value` lines; `#` and `!`
start comments. Important keys include:

| Key | Purpose |
| --- | --- |
| `api.store_wall_url` | Restaurant listing endpoint |
| `api.address_lookup_url` | Address resolution endpoint |
| `api.app_version`, `api.api_version` | Provider web-client version pins |
| `api.client_info`, `api.user_agent` | Web-client identity headers |
| `api.page_size` | Stores requested per page |
| `defaults.city_name`, `defaults.city_code` | Default CLI city |
| `defaults.address` | Optional default delivery address |
| `defaults.timeout` | HTTP timeout in seconds |
| `defaults.limit` | Default CSV row limit |
| `defaults.sort` | Default ranking (`distance`, `rating`, or `delivery_time`) |

## Output

The CSV is UTF-8 with a BOM so it opens correctly in Excel:

| Column | Meaning |
| --- | --- |
| `name` | Restaurant name |
| `rating_percent` | Rating percentage shown by the provider, empty if unrated |
| `votes` | Number of ratings, `1000` for `(1k+)` |
| `cuisine` | Provider food-type tag |
| `eta` | Delivery estimate |
| `distance` | Distance shown in the listing |
| `delivery_fee` | Effective delivery fee (`Free`, `0,49 €`, ...) |
| `url` | Link to the store page |

Example:

```csv
name,rating_percent,votes,cuisine,eta,distance,delivery_fee,url
Spaccanapoli Balmes,100,165,Italian,30-40 min,<100m,Free,https://example.com/stores/spaccanapoli-balmes
Chicago's Pizza Factory,100,109,Italian,30-40 min,<100m,Free,https://example.com/stores/chicagos-pizza-factory
```

## Providers

The application and domain layers never import provider-specific code. To add a
provider, implement `RestaurantProvider` (`location`, `cuisine_names`, and
`find_restaurants`) in a new outbound adapter, then wire it into the CLI
composition root. The provider's cuisine lookup, filters, pagination,
availability handling, and response mapping belong in that adapter.

The default `GlovoClient` adapter in
[`restaurants/adapters/outbound/`](restaurants/adapters/outbound/) is the only
place that knows about Glovo endpoints, headers, and response shapes. The
provider-neutral application pipeline then ranks and limits the returned
`Restaurant` objects.

See [docs/architecture.md](docs/architecture.md) for the system and sequence
diagrams, module map, stage reference, extension guide, API assumptions,
troubleshooting, and maintenance checklist.

## Tests

```bash
python -m unittest discover -s tests
```

## Notes

- Data comes from the default provider's public web store-listing and
  address-lookup endpoints. They are not officially documented and may change
  without notice.
- A single run makes a few requests (one per 50 restaurants plus one for the
  cuisine list, and one address lookup if `--address` is used), so it is polite
  to the site. Avoid running it in a tight loop.
- Restaurants are returned for the selected city or delivery address. Some
  stores may still not be available at every address within that area.
