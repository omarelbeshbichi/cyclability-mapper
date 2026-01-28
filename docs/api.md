# API documentation

The public HTTP API exposed by the system is here briefly described. The API provides read-only access to computed cyclability metrics per segment and related city network features. The API is implemented using FastAPI and, therefore, it automatically creates interactive documentation at runtime (GET /api/docs).

## API structure

The application exposes three top-level services:

- `/api`: access to computed data (described below).

- `/maps`: interactive exploration of results via maps rendered in Kepler.gl.

- `/figures`: key result figures.

Only the `/api` service is considered part of the stable API interface, while `/maps` and `/figures` are considered as a simple frontend - see `frontend` documentation.

## City Name

API endpoints are explicitly called by city name (path parameter). Multiple cities may be available. City names must match those used during ingestion.

## Segment endpoint
```
GET /api/segments/{city_name}/{osm_id}
```
Returns data from the road segment corresponding to `osm_id` within the specified city `city_name`.