"""
Module providing functions to ingest OSM data.
"""

import pandas as pd
import geopandas as gpd
import json
from pathlib import Path
import logging
import geopandas as gpd

def load_json_from_path(path: str) -> dict:
    """
    Load JSON file after performing preliminary checks and return it as a dictionary.
    
    Parameters
    ----------
    path: str
        Path to the JSON file to load

    Returns
    -------
    dict
        A dictionary where each key corresponds to a JSON feature
        Items include all associated properties
    """

    p = Path(path)

    # Path checks
    if not p.exists():
        raise FileNotFoundError(f'The specified path does not refer to any existing file: {path}')

    if p.is_dir():
        raise IsADirectoryError(f'Path refers to a directory, please specify path of a valid file: {path}')

    # Check file type
    if p.suffix.lower() not in ['.geojson', '.json']:
        raise ValueError(f'Unsupported file format: {p.suffix}. Expected .json (.geojson) type')

    logging.info(f'Path validated, proceeding with loading file: {p}')

    # Read JSON file
    with open(p, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f'Failed to parse JSON file {p}: {e}')

    return data

def feature_collection_to_dataframe(data: dict) -> pd.DataFrame:
    """
    Load dictionary containing GeoJSON data and return it normalized as a pandas DataFrame.
    
    Parameters
    ----------
    data: dict
        Dictionary storing GeoJSON data.

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame where each row corresponds to a GeoJSON feature
        Columns include feature ID, feature geometry, and all associated properties

    Notes:
        - The 'geometry' column contains the OSM GeoJSON standard geometry dictionary (type, coordinates)
    """

    # Validate data type
    if data.get('type') != 'FeatureCollection':
        raise ValueError(f'GeoJSON file provided is not a FeatureCollection')

    # Load data into a DataFrame
    features = data.get('features')
    if not isinstance(features, list):
        raise ValueError('Features are not available in GeoJSON FeatureCollection')
    df = pd.DataFrame(features)

    # Normalize dataframe
    if 'properties' in df:
        properties_normalized = pd.json_normalize(df['properties'])
    else:
        raise ValueError(f'Missing properties in GeoJSON file')

    # Concatenate parts
    df = pd.concat([df['geometry'], properties_normalized], axis = 1)

    return df

def geojson_to_gdf(geojson_dict: dict) -> gpd.GeoDataFrame:
    """
    Convert GeoJSON dictionary to GeoDataFrame.

    Missing values are replaced with None to be compatible with data pipeline
    
    Parameters
    ----------
    geojson_dict: dict 
        A valid GeoJSON object from parsing of overpass API JSON

    Returns
    -------
    gpd.GeoDataFrame 
        GeoDataFrame with CRS EPSG:4326 and missing values as None
    """

    gdf = gpd.GeoDataFrame.from_features(
        geojson_dict["features"],
        crs="EPSG:4326"
    )

    # Use None for missing value in database
    gdf = gdf.where(gdf.notna(), None)

    return gdf

def geojson_to_gdf_from_path(path: str) -> gpd.GeoDataFrame:
    """
    Load GeoJSON file from path and return it as a GeoDataFrame.
    
    Parameters
    ----------
    path: str
        Path to the JSON file to load

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame storing GeoJSON data
    """

    # Define path
    p = Path(path)
    
    # Path checks
    if not p.exists():
        raise FileNotFoundError(f'The specified path does not refer to any existing file: {path}')

    if p.is_dir():
        raise IsADirectoryError(f'Path refers to a directory, please specify path of a valid file: {path}')

    # Check file type
    if p.suffix.lower() not in ['.geojson', '.json']:
        raise ValueError(f'Unsupported file format: {p.suffix}. Expected .json (.geojson) type')

    logging.info(f'Path validated, proceeding with loading file: {p}')

    # Read JSON into GeoDataFrame
    gdf = gpd.read_file(p)

    return gdf