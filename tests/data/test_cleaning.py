import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from city_metrics.data.normalize.cleaning import restrict_gdf, parse_maxspeed_to_kmh, normalize_maxspeed_info, prepare_cyclability_segment
from pathlib import Path
import math
from city_metrics.domain.segment import CyclabilitySegment

# Used to generate a test GeoDataFrame
def make_test_gdf():
    """
    Define test GeoDataFrame to perform tests with
    """
    
    return gpd.GeoDataFrame({
        "highway": ["footway", "primary", "motorway", "residential", "footway"],
        "bicycle": [None, "yes", "yes", "yes", None],
        "geometry": [LineString([(0,0),(1,0)])]*5,
        "osm_id":[1,2,3,4, 5],
        "wikidata":[None]*5,
        "smoothness":[None]*5,
        "crossing":[None]*5,
        "lit": ["yes", "no", "yes;no", "limited", "yes"],
        "cycleway": [None, "lane", "lane", None, None],
        "cycleway:left": [None, None, None, "track", "lane"],
        "oneway": [None, "yes", None, None, None]
    })

def test_restrict_gdf():
    gdf = make_test_gdf()

    restricted = restrict_gdf(gdf)

    # Only "primary" highway should remain
    assert len(restricted) == 2 # primary and residential
    assert restricted.iloc[0]["highway"] == "primary"

def test_parse_maxspeed_to_kmh():

    assert math.isclose(parse_maxspeed_to_kmh("20"), 20, rel_tol=1e-6)
    assert math.isclose(parse_maxspeed_to_kmh("20 "), 20, rel_tol=1e-6)
    assert math.isclose(parse_maxspeed_to_kmh("20 mph"), 32, rel_tol=1e-6)
    assert math.isclose(parse_maxspeed_to_kmh("20mph"), 32, rel_tol=1e-6)
    assert math.isclose(parse_maxspeed_to_kmh("20 knots"), 37, rel_tol=1e-6)
    assert math.isclose(parse_maxspeed_to_kmh("20knots"), 37, rel_tol=1e-6)

def test_normalize_maxspeed_info():
    
    gdf = make_test_gdf()
    gdf["maxspeed"] = ["20", "20 mph", "20 knots", None, pd.NA]

    expected = ["20", "32", "37", None, None]

    normalized_gdf = normalize_maxspeed_info(gdf)
    normalized_maxspeed = normalized_gdf["maxspeed"].tolist()

    for a, b in zip(normalized_maxspeed, expected):
        if b is None:
            assert pd.isna(a)
        else:
            assert a == b

def test_prepare_cyclability_segment():

    gdf = make_test_gdf()

    excellent_bike_infra = {
        "cycleway",
        "track",
        "track;lane",
        "traffic_island",
        "link",
        "separate"
    }

    # Test with second row of gdf
    segment = prepare_cyclability_segment(gdf.iloc[1], excellent_bike_infra)

    assert isinstance(segment, CyclabilitySegment)
    assert segment.lighting == "no"
    assert segment.highway == "primary"
    assert segment.bike_infrastructure == "lane"

    assert segment.missing_info == {
        "maxspeed": True,
        "surface": True,
        "lighting": False
    }

    assert segment.oneway == "yes"

    segment = prepare_cyclability_segment(gdf.iloc[3], excellent_bike_infra)

    assert segment.bike_infrastructure == "track"
