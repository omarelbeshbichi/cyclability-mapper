# Kepler.gl Maps Access

The application is using FastAPI to serve metrics results via a dedicated endpoint `/maps`. Maps are then constructed using city network data and computed data within the database, and visualized using the Kepler.gl open-source framework.

## Map Endpoint
```
GET /maps/{city_name}
```
Returns Kepler.gl map of segment-level cyclability metrics of the specified city `city_name`.

![alt text](/media/kepler_map_example.png)

## Mouse Hovering Data
Mouse pointer data provides for each segment:
- `osm_id`
- cyclability score
- segment length
- features scores (unweighted)

![alt text](/media/kepler_map_hover_example.png)

## JSON Config
Kepler.gl makes use of a dedicated JSON config file defining most rendering options.


# Figures

The application is returning a few key figures via a dedicated endpoint `figures`.

## Scatter Table
```
GET /figures/metrics_scatter
```

Returns scatter table of total city scores as a function of total city uncertainty for all the cities present in the database.

![alt text](/media/metrics_scatter_example.png)

## Sensitivity Figures (Experimental)

Group weights are qualitative judgement about what aspects of cyclability matter the most. They are not objective truths, but modeling choices. As such, it may be useful to see how sensitive is final result to weights themselves.

Sensitivity analysis shows how much the city’s score depends on subjective modeling choices about what aspects of cycling matter most.

The application provides experimental sensitivity analysis figures showing how changes in group weights affect city cyclability metrics. These are available via dedicated endpoints.

**Line plots per group**: total city score vs delta group weight. If line barely moves -> city score stable to qualitative judgement.
```
GET /figures/group_sensitivity/{city_name}
```

**Heatmaps**: sensitivity of city score to group weight variations for all cities available in sensitivity table in database `group_sensitivity`.
```
GET /figures/group_sensitivity/heatmap
```

These figures are intended for diagnostic purposes and exploration only.