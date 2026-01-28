# Database Schema

## Network Segments

The primary table is `network_segments` and is used as authoritative representation of the city network. It is populated with information from `CyclabilitySegments` objects.

Geometries are stored as LineStrings in EPSG:4326.

Attributes correspond to those defined in `CyclabilitySegments`, with the addition of `city_name` to store segment networks from multiple cities.

Database services implemented allow for recomputing metrics or refreshing data from saved Polygon for a given city - see below.

The combination of (`city_name`, `osm_id`) is enforced as unique.  

GIST index is also defined for quick geometry access by PostGIS.

# Segment Metrics

The `segment_metrics` table stores metrics associated with each segment. The foreign key `segment_id` references `network_segments(id)` with cascading deletes.

For each segment, the table stores:
- metric name and version
- cyclability score
- missing features
- `metric_feature_scores`: Unweighted cyclability score component from each feature. They are returned unweighted to provide a clear indication of which mapped value [0-1] a given feature possesses. 

Metadata field is currently unused.

# Refresh Areas

The `refresh_areas` table stores the Polygon used to retrieve OSM data for each city. Only one Polygon per city is allowed.

A creation timestamp and a GIST index on geometry are defined.

# City Metrics

The `city_metrics` table stores aggregated city-level metrics and uncertainty information. Only one row per city and metric version is allowed.

Stored attributes include:
- total city score
- total uncertainty
- per-feature uncertainty contributions
- creation timestamp

# v_cyclability_segment_detail

This virtual view is used by services and the API to retrieve the latest metrics data.

It is defined by first selecting the most recent metric version using a helper table (`latest_metric`) and then joining the corresponding segment and metric data. For now selecting based on version is redundant - only one version is effectively present per city - but may be useful for later.