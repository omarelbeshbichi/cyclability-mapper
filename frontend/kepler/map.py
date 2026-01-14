from keplergl import KeplerGl
from cmm.services.segments import load_segments_for_viz
from cmm.utils.config_reader import read_config

def create_map(kepler_config_path: str = None):

    config = read_config("kepler", "json", kepler_config_path)

    gdf = load_segments_for_viz()
    gdf = gdf.rename_geometry("geometry")

    # Compute bounding box and center map to given data
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lon = (bounds[0] + bounds[2]) / 2
    center_lat = (bounds[1] + bounds[3]) / 2

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