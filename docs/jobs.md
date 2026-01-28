# build_network

Main package job. It can be called in two ways.

## Municipal Boundary using City Name
```bash
docker compose exec app python -m city_metrics.jobs.build_network --c oslo --cc no --chunk 5000 --tout 50 --tol 0.0005
```
where:
- `--c` is the city name
- `--cc` is the country code (ISO-2)
- `--chunk` (optional) is the maximum number of segments per chunk to be processed in one go
- `--tout` (optional) is the timeout time used during API fetch
- `--tol` (optional) is the tolerance used to simplify city outline Polygon before fetch

This will use a Polygon describing the city's municipal boundaries to fetch data from the OSM API.

## Bounding Box
```bash
docker compose exec app python -m city_metrics.jobs.build_network --c oslo --south 59.898941 --west 10.667409 --north 59.954596 --east 10.815038 --chunk 5000 --tout 50 --tol 0.0005
```

This will use an explicit bounding box, normally defined with four numbers representing the South Latitude, North Latitude, West Longitude, and East Longitude. The example is using a bounding box around the area of Oslo, Norway.

In both cases, the city name provided by `--c` parameter is used to define the city name in the database, while no country code information is retained. This means that for now, the database is not able to store cities with the same name.

# recompute_metrics
Recomputes metrics data related to a specific city starting from network data stored in `network_segments`.

```bash
docker compose exec app python -m city_metrics.jobs.recompute_metrics --c oslo
```

All metric data in the database for the given city is overwritten (`segment_metrics` and `city_metrics`).

# refresh_osm_data
Refreshes all data related to a given city from the associated Polygon saved in the database and recomputes associated metrics.

```bash
docker compose exec app python -m city_metrics.jobs.refresh_osm_data --c oslo --chunk 5000 --tout 50
```

# list_cities
Lists all cities available in the database.

```bash
docker compose exec app python -m city_metrics.jobs.list_cities
```

# list_city_metrics
Lists all aggregated city metrics results available in the database (table `city_metrics`).

```bash
docker compose exec app python -m city_metrics.jobs.list_city_metrics
```

# delete_network
Delete all data associated with the given city.

```bash
docker compose exec app python -m city_metrics.jobs.delete_network --c oslo
```