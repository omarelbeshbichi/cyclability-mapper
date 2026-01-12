from keplergl import KeplerGl
from .load_data import load_segments
from cmm.utils.config_reader import read_config

def create_map(user="user", host="localhost", password="pass", database="db", kepler_config_path: str = None):

    config = read_config("kepler", "json", kepler_config_path)

    gdf = load_segments(user, host, password, database)
    gdf = gdf.rename_geometry("geometry")

    m = KeplerGl(height=800)

    # Apply data and configurations
    m.add_data(gdf, "segments")
    m.config = config

    return m