import geopandas as gpd
import pandas as pd
from pathlib import Path
from cmm.data.ingest.geojson_loader import load_json_from_path, feature_collection_to_dataframe, geojson_to_gdf_from_path


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
