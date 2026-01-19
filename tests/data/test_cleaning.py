import geopandas as gpd
from shapely.geometry import LineString
from cmm.data.normalize.cleaning import restrict_gdf
from pathlib import Path

# Used to generate a test GeoDataFrame
def make_test_gdf():
    return gpd.GeoDataFrame({
        "highway": ["footway", "primary", "motorway", "bus_guideway"],
        "bicycle": [None, "yes", "yes", "yes"],
        "geometry": [LineString([(0,0),(1,0)])]*4,
        "osm_id":[1,2,3,4],
        "wikidata":[None]*4,
        "smoothness":[None]*4,
        "crossing":[None]*4
    })

def test_restrict_gdf_filters():
    gdf = make_test_gdf()

    restricted = restrict_gdf(gdf)

    # Only "primary" highway should remain
    assert len(restricted) == 1
    assert restricted.iloc[0]["highway"] == "primary"
