from keplergl import KeplerGl
from cmm.services.segments import load_segments_for_viz
from cmm.utils.config_reader import read_config

def create_map(city_name: str, 
               kepler_config_path: str = None):

    config = read_config("kepler", "json", kepler_config_path)

    gdf = load_segments_for_viz(city_name)
    gdf = gdf.rename_geometry("geometry")

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

    # Apply data
    m.add_data(gdf, "segments")

    return m