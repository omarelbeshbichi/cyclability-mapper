import geopandas as gpd
import pandas as pd
from pathlib import Path
from cmm.data.ingest.geojson_loader import load_json_from_path, feature_collection_to_dataframe, geojson_to_gdf_from_path
from cmm.data.ingest.overpass_parser import overpass_elements_to_geojson
from cmm.data.ingest.overpass_client import run_overpass_query
from unittest.mock import Mock, patch

def test_load_json_from_path(dev_geojson_path):

    data = load_json_from_path(dev_geojson_path)

    assert data['type'] == 'FeatureCollection'
    #assert len(data['features']) == 1

def test_feature_collection_to_dataframe(dev_geojson_path):
    
    data = load_json_from_path(dev_geojson_path)

    df = feature_collection_to_dataframe(data)
    assert isinstance(df, pd.DataFrame)
    assert "name" in df.columns
    assert "geometry" in df.columns

def test_geojson_to_gdf_from_path(dev_geojson_path):

    gdf = geojson_to_gdf_from_path(dev_geojson_path)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert not gdf.empty

def test_overpass_elements_to_geojson():
    
    # Define dummy elements list
    elements = [
        # Good element
        {
            "type": "way",
            "id": 1,
            "geometry": [
                {"lat": 59.0, "lon": 10.0},
                {"lat": 59.1, "lon": 10.1},
            ],
            "tags": {"highway": "residential"},
        },
        # Point
        {
            "type": "node", 
            "id": 2,
        },
        # Degenerate geometry
        {
            "type": "way",
            "id": 3,
            "geometry": [  
                {"lat": 59.2, "lon": 10.2},
            ],
        },
    ]

    geojson = overpass_elements_to_geojson(elements)

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1 # Only one good element should be parsed

    # Collect features of first element
    feature = geojson["features"][0]

    assert feature["type"] == "Feature"
    assert feature["id"] == "way/1"
    assert feature["properties"]["@id"] == "way/1"
    assert feature["properties"]["highway"] == "residential"

    assert feature["geometry"]["type"] == "LineString"
    assert feature["geometry"]["coordinates"] == [
        [10.0, 59.0],
        [10.1, 59.1],
    ]

def test_run_overpass_query():
    # Mock the requests.post HTTP connection
    mock_response = Mock()
    mock_response.json.return_value = {"elements": []} # provide dummy return value API
    mock_response.raise_for_status.return_value = None

    # Define patch
    with patch("requests.post", return_value = mock_response) as mock_post:
        result = run_overpass_query("dummy query")

    mock_post.assert_called_once()
    assert result == {"elements": []}