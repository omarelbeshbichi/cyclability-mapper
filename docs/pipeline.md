# Build Pipeline

In the following, the pipeline workflow to build a segment network for a city, including associated cyclability metrics, is laid out.

# Area Definition

Code associated with this section is stored in `src/cmm/data/ingest/geocoding`.

The pipeline can be initialized using CLI jobs stored in `src/cmm/jobs`. The main job, here described, is called `build_network`. The pipeline can be called in two ways:
- by providing an explicit bounding box, normally defined with four numbers representing the South Latitude, North Latitude, West Longitude, and East Longitude. For example, for the area of Oslo, Norway - ["59.85", "60.05", "10.60", "10.85"].
- by providing a city name and associated ISO-2 country code (for example: "oslo", "no"). This is used in the pipeline to resolve an administrative polygon using Nominatim. 
  NB: I have noted that Nominatim, in some instances, resolves the provincial polygon instead of the one relative to the city administrative area.

Both ways essentially define a reference Polygon, which is used in the next step of the pipeline.

# OSM Ingestion

Code associated with this section is stored in overpass files in `src/cmm/data/ingest/overpass_*.py`.

An overpass API query is defined using the Polygon just established. To improve query size, the Polygon is simplified using a defined tolerance defined with the optional CLI parameter `-tol` (default: 0.0005). The fetch timeout in seconds can also be set using the optional CLI parameter `--tout` (optional: 50 s). The query fetches all data relative to `way` objects of type `highway` - that is, all streets within the Polygon. An Overpass API client is defined using the `requests` module. Connection retries and delay are also included. Missing YAML mapping data are automatically prompted from user in CLI environment and used to update YAML table. Raw JSON data fetched from the API service is converted to standard GeoJSON format, and from GeoJSON to a raw GeoPandas GeoDataFrame.

# Processing in Chunks

Note that the normalization, computation, and database processes are divided in ´chunks´ to improve memory usage. Default chunk size is 5000 (segments per chunk), and it can be set with the optional CLI parameter `--chunk` in `build_network` and `refresh_osm_data` jobs - see JOBS documentation.

# Data Normalization

Code associated with this section is stored in `src/cmm/data/normalize/cleaning`.

The raw GeoDataFrame defined from data fetched from Overpass API is first validated by checking the presence of valid geometry for all segments. Maximum traffic speed data is also normalized to handle different units and lack of data. The GeoDataFrame is then restricted by filtering out unnecessary and irrelevant types.

Data necessary for the metrics calculation are then extracted from each GeoDataFrame row (function `prepare_cyclability_segment`) and stored in a `CyclabilitySegment` object. Info about missing data of `surface`, `maxspeed`, and `lighting` features for each segment is collected and stored in feature `missing_info` within the `CyclabilitySegment` object.

The segment is then used to compute the cyclability index as explained in the next step of the pipeline, and later to define a final GeoDataFrame including CyclabilitySegment data and the computed metrics itself.

# Metrics Computation

Code associated with this section is stored in `src/cmm/metrics/compute_metrics`.

The segment-level cyclability metrics is computed starting from `CyclabilitySegment` by using data of `bike_infrastructure`, `surface`, `maxspeed`, and `lighting`. Data is scaled to [0-1] domain using a min-max scaling table defined in a dedicated YAML. Weighting information for each feature is also collected from a dedicated YAML file. More info in metrics documentation.  

An aggregated cyclability metric for the entirety of the city network is computed by performing a length-weighted average of the segment-level metrics.

Aggregated uncertainty information of the city for each feature is also computed by using a length-weighted average of `missing_info` multiplied for the relative feature weight. A global city uncertainty parameter is defined as the sum of all feature uncertainties. More info in metrics documentation.

# Data Storage

Segments, metrics, and reference areas are stored in a PostGIS database defined by a `network_segments` primary table, a `segment_metrics` table storing metrics data, a `refresh_areas` table to store associated Polygons, and a `city_metrics` table to store aggregated city metrics and associated uncertainty. More info in the database documentation.