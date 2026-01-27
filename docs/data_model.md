# Network Segments

Each road in a city network is represented as a segment. The project defines a base dataclass `Segment` and a derived dataclass `CyclabilitySegment`, located in `src/cmm/domain/segment`. 

A segment stores all (and only) the information necessary for cyclability metrics computation. All features are normalized to a standard internal representation and prepared for min-max scaling to the [0-1] range using transformation tables defined in dedicated `YAML` files.

Only OSM `way` objects of type `highway` are ingested. Other OSM object types are ignored.


## CyclabilitySegment Structure

Authoritative data (from OSM):
- `osm_id`: OSM identifier of the segment.
- `name`: street name.
- `geometry`: LineString geometry in EPSG:4326.
- `maxspeed`: maximum traffic speed. 
- `surface`: surface quality.
- `lighting`: light conditions.
- `highway`: OSM highway type classification.

Derived features:
- `segment_length`: segment length in meters, computed as WGS84 geodesic length.
- `bike_infrastructure`: cycling infrastructure quality, derived from OSM `cycleway` tags during normalization.
- `oneway`: cycling-relevant oneway condition. Assumed "yes" if cycling is effectively one-way, "no" otherwise.

Output fields:
- `cyclability_metrics`: computed cyclability score for the segment.
- `missing_info`: dictionary tracking missing data for maxspeed, surface, and lighting if missing from OSM database.


## Metrics

Each `CyclabilitySegment` stores the computed segment-level cyclability score in the field:

- `cyclability_metrics`: scalar score in the [0, 1] range

Metric values are computed during the pipeline run and stored in PostGIS. Metric versioning is handled separately - see metrics documentation.

## Missing data tracking

For the features (`maxspeed`, `surface`, `lighting`), the presence or absence of OSM information is tracked for each segment.

- `missing_info`: dictionary tracking feature names to binary missingness information

This information is used to compute aggregated uncertainty measures at the city level - see metrics documentation.