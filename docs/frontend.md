# Kepler.gl Maps Access

The application is using FastAPI to serve metrics results via a dedicated endpoint `/maps`. Maps are then constructed using city network data and computed data within the database, and visualized using the Kepler.gl open-source framework.

## Map Endpoint
```
GET /maps/{city_name}
```
Returns Kepler.gl map of segment-level cyclability metrics of the specified city `city_name`.

## Mouse Hovering Data
Mouse pointer data provides for each segment:
- `osm_id`
- cyclability score
- segment length
- features scores (unweighted)

## JSON Config
Kepler.gl makes use of a dedicated JSON config file defining most rendering options.


# Figures

The application is returning a few key figures via a dedicated endpoint `figures`.

## Scatter Table
```
GET /figures/metrics_scatter
```

Returns scatter table of total city scores as a function of total city uncertainty for all the cities present in the database.