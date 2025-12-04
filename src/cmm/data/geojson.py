"""
Module providing functions to load and process OSM GeoJSON files into pandas DataFrames. 
"""

import pandas as pd
import json
from pathlib import Path
import logging

def load_geojson(path: str) -> pd.DataFrame:
    """
    Load a GeoJSON file containing OSM data and return it as a pandas DataFrame.
    
    Parameters
    ----------
    path: str
        Path to the .geojson file to load

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame where each row corresponds to a GeoJSON feature
        Columns include feature ID, feature geometry, and all associated properties

    Notes:
        - The 'geometry' column contains the OSM GeoJSON standard geometry dictionary (type, coordinates)
    """

    p = Path(path)

    # Path checks
    if not p.exists():
        raise FileNotFoundError(f'The specified path does not refer to any existing file: {path}')

    if p.is_dir():
        raise IsADirectoryError(f'Path refers to a directory, please specify path of a valid file: {path}')

    # Check file type
    if p.suffix.lower() not in ['.geojson', '.json']:
        raise ValueError(f'Unsupported file format: {p.suffix}. Expected .geojson')

    logging.info(f'Path validated, proceeding with loading file: {p}')

    # Read JSON file
    with open(p, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f'Failed to parse JSON file {p}: {e}')

    # Check for GeoJSON feature collection type
    if data['type'] != 'FeatureCollection':
        raise ValueError(f'GeoJSON file provided is not a FeatureCollection')

    # Load data into a DataFrame
    if 'features' in data:
        df = pd.DataFrame(data['features'])
    else:
        raise ValueError('Features are not available in GeoJSON file')

    # Normalize dataframe
    if 'properties' in df:
        properties_normalized = pd.json_normalize(df['properties'])
    else:
        raise ValueError(f'Missing properties in GeoJSON file')

    # Concatenate parts
    df = pd.concat([df['geometry'], properties_normalized], axis = 1)

    return df