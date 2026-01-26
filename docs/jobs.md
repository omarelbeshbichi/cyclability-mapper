# build_network

Main package job. It can be called in two ways.

## Municipal Boundary using City Name
```bash
docker compose exec app python -m cmm.jobs.build_network --c oslo --cc no --chunk 5000
```
where:
- `--c`: city name
- `--cc`: country code (ISO-2)
- `--chunk`: optional, default 5000. Number of segments to be processed in one chunk. Used to improve memory usage.

This will use a Polygon describing the city municipal boundaries to fetch data from OSM API.

## Bounding Box
```bash
docker compose exec app python -m cmm.jobs.build_network --c oslo --south 59.898941 --west 10.667409 --north 59.954596 --east 10.815038
```

This will use an explicit bounding box, normally defined with four numbers representing the South Latitude, North Latitude, West Longitude, and East Longitude. The example is using a bounding box around the area of Oslo, Norway.

In both cases, the city name provided by `--c` parameter is used to define the city name in the database, while no country code information is retained. This means that for now the database is not able to store cities with the same name.

# recompute_metrics

Recomputes metrics data related to a specific city starting from network data stored in `network_segments`.

```bash
docker compose exec app python -m cmm.jobs.recompute_metrics --c oslo
```

All metrics data in database for given city is overwritten (`segment_metrics` and `city_metrics`).

# refresh_osm_data

Refreshes all data related to a given city from the associated Polygon saved in database and recomputes associated metrics.

```bash
docker compose exec app python -m cmm.jobs.refresh_osm_data --c oslo --chunk 5000
```

# list_cities

Lists all cities available in the database.

```bash
docker compose exec app python -m cmm.jobs.list_cities
```

# delete_network

Delete all data associated with given city.

```bash
docker compose exec app python -m cmm.jobs.delete_network --c oslo
```