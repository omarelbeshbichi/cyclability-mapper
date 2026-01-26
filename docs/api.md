# API documentation

The public HTTP API exposed by the system is here described. The API provides read-only access to computed segment-level cyclability metrics and related city network features. The API is implemented using FastAPI and, therefore, it automatically creates interactive documentation at runtime (GET /api/docs).

## API structure

The application exposes two top-level services:

- `/api`: access to computed data (described below).

- `/maps`: interactive exploration of results via maps rendered in Kepler.gl frontend.

Only the `/api` namespace is considered part of the stable programmatic interface, while `/maps` is considered as a simple frontend - see frontend documentation.

## City Name

API endpoints are explicitly scoped by city name (path parameter). Multiple cities can be available at the same time. City names must match those used during ingestion.

## Segment endpoint
```
GET /api/segments/{city_name}/{osm_id}
```
Returns road segment corresponding to `osm_id`  within the specified city `city_name`.