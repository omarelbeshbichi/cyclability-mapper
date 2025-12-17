"""
Module providing functions to normalize OSM data.
"""

import pandas as pd

def restrict_feature_collection(df: pd.DataFrame) -> pd.DataFrame:
    """
    Restrict raw OSM dataframe FeatureCollection by removing unnecessary features
    and preserving general schema.

    Parameters
    ----------
    data: pd.DataFrame
        Pandas DataFrame storing raw GeoJSON FeatureCollection.
    
    Returns
    -------
    data_filtered: pd.DataFrame
        Pandas DataFrame storing filtered GeoJSON FeatureCollection to be used in package pipeline.
    """

    # Filter out all highway = footway LineStrings with no bicycle designation
    # ~ -> keep all rows not complying with the mask
    mask = ~((df['highway'] == 'footway') & (df["bicycle"] != "yes"))
    df_filtered = df[mask]

    # Filter out motorways
    mask = ~((df_filtered['highway'] == 'motorway') | (df_filtered['highway'] == 'motorway_link'))
    df_filtered = df_filtered[mask]

    # Filter out irrelevant highway types
    mask = ~((df_filtered['highway'] == 'bus_guideway') | 
             (df_filtered['highway'] == 'escape') | 
             (df_filtered['highway'] == 'traceway') | 
             (df_filtered['highway'] == 'steps') |
             (df_filtered['highway'] == 'corridor') | 
             (df_filtered['highway'] == 'via_ferrata') |
             (df_filtered['highway'] == 'proposed') |
             (df_filtered['highway'] == 'construction'))
    df_filtered = df_filtered[mask]

    return df_filtered

