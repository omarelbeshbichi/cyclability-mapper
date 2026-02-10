from keplergl import KeplerGl
from city_metrics.services.segments import load_segments_for_viz
from city_metrics.utils.config_helpers import read_config

def create_map(city_name: str, 
               kepler_config_path: str = None):

    config = read_config("kepler", "json", kepler_config_path)

    gdf = load_segments_for_viz(city_name)
    gdf = gdf.rename_geometry("geometry")

    # Add rounding to segment length
    gdf["segment_length"] = gdf["segment_length"].astype(float).round(2)
    
    # Apply simplification of geometries
    gdf = gdf.to_crs(3857) # m
    gdf["geometry"] = gdf.geometry.simplify(tolerance=5, preserve_topology=True)
    gdf = gdf.to_crs(4326) # deg
    
    # Compute where map should be initialized
    city_geom = gdf.geometry.union_all()
    centroid = city_geom.centroid
    center_lon = centroid.x
    center_lat = centroid.y

    # Add start location (mapState)
    config.setdefault("config", {})["mapState"] = {
        "latitude": center_lat,
        "longitude": center_lon,
        "zoom": 12,
        "bearing": 0,
        "pitch": 0
    }

    # Initialize KeplerGL map + apply configuration setup
    m = KeplerGl(config = config)

    # Reduce data needed
    gdf = gdf[
        ["geometry", "osm_id", "total_score", "segment_length", "all_scores"]
    ]
    
    # Apply data
    m.add_data(gdf, "segments")

    return m