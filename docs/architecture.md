# Architecture and maintainer guide

This document explains how the application is put together, where behaviour
should live, and what to check when Glovo changes its private web API.

## High-level flow

```text
cli.main
  -> argparse arguments (cuisine, address, city, sort-by, limit, output)
  -> GlovoClient.fetch_restaurants(...)
       -> search pipeline
            resolve-cuisine
            build-filters
            fetch-store-entries
            filter-open
            build-restaurants
            rank-restaurants (distance | rating | delivery_time)
            limit-results
  -> cli.write_csv(...)
```

The pipeline is the core of the application. The CLI owns argument parsing and
rendering; the client owns HTTP concerns; pipeline stages own data
transformation.

## Package layout

| File | Responsibility |
| --- | --- |
| `glovo_restaurants/cli.py` | Argument parsing, user-facing messages, CSV output, exit codes. |
| `glovo_restaurants/client.py` | Glovo HTTP transport: headers, location resolution, pagination, response validation. |
| `glovo_restaurants/config.py` | Typed settings loader and validation for `config.properties`. |
| `glovo_restaurants/config.properties` | API endpoints, client identity/version pins, pagination, and CLI defaults. |
| `glovo_restaurants/search.py` | Search context, pipeline stages, and the default search pipeline. |
| `glovo_restaurants/pipeline.py` | Generic `Pipeline` and `PipelineStep` primitives with no Glovo-specific logic. |
| `glovo_restaurants/models.py` | `Restaurant` model, API-to-model mapping, parsing helpers, ranking. |
| `glovo_restaurants/__init__.py` | Public package API. Keep this small and stable. |
| `tests/` | Unit tests; no live network calls are required. |

## Pipeline contract

`pipeline.Pipeline` is an immutable ordered sequence of steps:

```python
@dataclass(frozen=True)
class Pipeline(Generic[ContextT]):
    steps: tuple[PipelineStep[ContextT], ...]

    def run(self, context: ContextT) -> ContextT:
        for step in self.steps:
            step.run(context)
        return context
```

A step is any object with a `name` attribute and a `run(context)` method.
Steps mutate the shared `SearchContext` and return `None`. Keeping this
contract narrow makes stages easy to test and reorder.

`SearchContext` carries the request and intermediate results:

| Field | Written by | Meaning |
| --- | --- | --- |
| `client` | caller | The `GlovoClient` used for transport. |
| `cuisine` | caller | User-supplied cuisine query. |
| `sort_by` | caller | Ranking strategy: `distance` (default), `rating`, or `delivery_time`. |
| `limit` | caller | Maximum results after ranking, or `None` for all. |
| `filter_id` | `resolve-cuisine` | Glovo food-type filter id. |
| `filters` | `build-filters` | JSON filters sent to the store-wall endpoint. |
| `entries` | fetch/filter stages | Raw store entries from Glovo. |
| `restaurants` | build/rank/limit stages | Final typed results. |

## Ranking

`models.sort_restaurants` supports three strategies:

| `sort_by` | Ordering |
| --- | --- |
| `distance` (default) | Parsed distance ascending, then rating, votes, name. |
| `rating` | Rating descending, votes descending, then closest, name. |
| `delivery_time` | ETA midpoint ascending, then closest, rating, votes, name. |

Distance is parsed from strings such as `<100m`, `1.2km`, or `1,2 km`. ETA is
parsed from strings such as `30-40 min` (midpoint), `20 min`, `1h 10 min`, or
`1-2 h`. Unparseable values are treated as missing and sorted last.

## Default search stages

| Stage | Input | Output | Notes |
| --- | --- | --- | --- |
| `ResolveCuisineStep` | `cuisine` | `filter_id` | Uses case/punctuation-insensitive matching and typo suggestions. |
| `BuildFiltersStep` | `filter_id` | `filters` | Requests the cuisine filter and Glovo's rating sort; final ranking is local. |
| `FetchStoreEntriesStep` | `filters` | `entries` | Delegates pagination and deduplication to `GlovoClient.fetch_store_entries`. |
| `FilterOpenStep` | `entries` | `entries` | Keeps only stores whose `availability.status` is `OPEN`. |
| `BuildRestaurantsStep` | `entries` | `restaurants` | Maps API payloads to `Restaurant`; uses client city/country/language for URLs. |
| `RankRestaurantsStep` | `restaurants`, `sort_by` | `restaurants` | Closest first by default; rating or ETA when requested. Missing values go last. |
| `LimitResultsStep` | `restaurants`, `limit` | `restaurants` | Applied after ranking so the limit is meaningful. |

`build_search_pipeline()` is the single place that defines stage order. If you
need custom behaviour, compose a new pipeline rather than branching inside a
stage.

### Adding a stage

1. Create a class with a unique `name` and a `run(context)` method.
2. Read and write only the context fields the stage owns.
3. Raise a `GlovoError` subclass for user-facing failures.
4. Add the stage to `build_search_pipeline()` in the correct position.
5. Add a focused test in `tests/test_pipeline.py`.

Example:

```python
class DropChainsStep:
    name = "drop-chains"

    def run(self, context: SearchContext) -> None:
        context.entries = [
            entry for entry in context.entries
            if entry.get("isChain") is not True
        ]
```

Then insert `DropChainsStep()` before `BuildRestaurantsStep()`.

### Replacing the pipeline

`GlovoClient` stores its pipeline in `search_pipeline`. This is the preferred
seam for tests or embedders:

```python
client.search_pipeline = Pipeline(
    (ResolveCuisineStep(), BuildFiltersStep(), FetchStoreEntriesStep())
)
```

## Client responsibilities

`GlovoClient` is a transport adapter. It should not know about ranking, CSV
formatting, or user-facing messages. Its jobs are:

- Build the required `glovo-*` headers.
- Resolve an optional delivery address to coordinates and a city code.
- Page through the store-wall endpoint and deduplicate store ids.
- Raise typed errors for request and response failures.

Important implementation details:

- `fetch_store_entries()` is the pagination boundary. Availability filtering
  happens later in the pipeline so transport code stays reusable.
- `_resolve_location()` runs lazily on the first request. It appends the city
  to the address only when the city is not already present.
- The address and coordinates are cached for the lifetime of the client.
- `api.page_size` in `config.properties` controls how many stores are requested per HTTP call.

## Glovo API assumptions

These are unofficial web endpoints and can change without notice. Edit
`glovo_restaurants/config.properties` first; `config.py` validates the values
and `client.py` consumes them.

| Property | Purpose |
| --- | --- |
| `api.store_wall_url` | Store-wall/category endpoint. |
| `api.address_lookup_url` | Public address autocomplete/resolution endpoint. |
| `api.client_info`, `api.app_version`, `api.api_version` | Spoofed web-client identity headers. |
| `api.request_ttl`, `api.referer`, `api.user_agent` | Request identity/transport headers. |
| `api.page_size` | Stores requested per pagination call. |
| `defaults.*` | CLI/client city, country, language, timeout, limit, and sort defaults. |

Request identity headers include device/session/client UUIDs generated per
client instance and timestamps refreshed per request. The delivery location is
expressed through:

- `glovo-location-city-code`
- `glovo-location-country-code`
- `glovo-delivery-location-latitude`
- `glovo-delivery-location-longitude`
- `glovo-delivery-location-accuracy`
- `glovo-delivery-location-timestamp`

When the API changes, verify these areas in order:

1. A single store-wall request still returns `data.stores.entries`.
2. Pagination still accepts `offset`, `limit`, and `previousStoreIds`.
3. Availability is still `entry["availability"]["status"]`.
4. Address lookup still returns `addresses[]` with `latitude`, `longitude`,
   `cityCode`, and `countryCode`.
5. The pinned `glovo-app-version` still returns `200` rather than `403`.

## Error handling and exit codes

`GlovoError` covers runtime API/search failures:

- `CuisineNotFoundError`: unknown cuisine; includes suggestions when possible.
- `AddressNotFoundError`: address lookup succeeded but no geocodable match.
- `GlovoError`: transport, unexpected response, or address lookup failures.

`ConfigurationError` is raised by `config.py` for missing files, missing keys,
unparseable values, or invalid defaults. The CLI reports it as a configuration
error and exits with code `1`.

The CLI maps errors as follows:

| Condition | Exit code |
| --- | --- |
| Success | `0` |
| No restaurants found or Glovo/address failure | `1` |
| Unknown cuisine | `2` |
| Invalid arguments | `2` (argparse) |
| Invalid/missing configuration | `1` |

Branch on exception types, not message text. If a new user-facing failure mode
is needed, add a `GlovoError` subclass and handle it in `cli.main`.

## Testing strategy

Run the suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

Guidelines:

- Unit tests must not call the live Glovo API.
- `tests/test_client.py` uses a fake client/session to test pagination, address
  headers, and closed-store filtering.
- `tests/test_config.py` covers properties parsing, validation, overrides, and
  client settings wiring.
- `tests/test_pipeline.py` tests the pipeline contract and the default stage
  composition.
- `tests/test_models.py` covers rating/votes/distance/ETA parsing and all ranking strategies.
- When changing a stage, add a test at the stage or pipeline level. When
  changing transport, add a test with a fake session.

For an occasional live smoke test:

```bash
python -m glovo_restaurants --cuisine italian --address "Carrer de Casp 111" --limit 3
python -m glovo_restaurants --cuisine italian --sort-by delivery-time --limit 3
```

Avoid running live requests in a tight loop.

## Maintenance checklist

Before merging a change:

- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] New behaviour is implemented as a pipeline stage, not in the CLI.
- [ ] HTTP changes stay inside `GlovoClient`.
- [ ] Public functions/classes have docstrings.
- [ ] CLI help, `README.md`, and `config.properties` describe the current options.
- [ ] Version/identity changes are made in `config.properties`, not hard-coded.
- [ ] Closed-store handling still happens before ranking and limiting.
- [ ] The default ranking remains closest-first and every `--sort-by` option has a test.
- [ ] No secrets or personal addresses are committed to fixtures.

## Configuration resolution

`config.default_config_path()` selects the first available source:

1. `GLOVO_CONFIG` environment variable.
2. `config.properties` in the current working directory.
3. `config.properties` at the source checkout root.
4. The packaged `glovo_restaurants/config.properties`.

`get_settings()` caches the result for the process. Tests and embedders that
need isolated settings should call `load_settings(path)` or pass a `Settings`
instance to `GlovoClient`.

## Known limitations

- Glovo's web API is unofficial and version-pinned.
- Address matching depends on Glovo's autocomplete; ambiguous addresses may
  need a street number or postal code.
- City-only searches rely on the supplied `--city-code`; use `--address` when
  the city code is unknown.
- Some stores may be visible for a city but not deliverable to every address.
- Distance/ETA ranking depends on the display strings Glovo returns; unknown
  or unexpected formats are placed after parseable values.
- The CSV writer is a terminal adapter, not a pipeline stage. If output grows
  (for example JSON or a database sink), introduce a separate output pipeline
  rather than coupling it to search.
