"""
Module providing functions to normalize OSM data.
"""

import geopandas as gpd

def restrict_feature_collection(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Restrict raw OSM GeoDataFrame FeatureCollection by removing unnecessary and
    filtering irrelevant types.

    Parameters
    ----------
    data: gpd.GeoDataFrame
        GeoPandas GeoDataFrame storing raw GeoJSON FeatureCollection.
    
    Returns
    -------
    data_filtered: gpd.GeoDataFrame
        GeoPandas GeoDataFrame storing filtered GeoJSON FeatureCollection to be used in package pipeline.
    """

    # Filter out all highway = footway LineStrings with no bicycle designation
    # ~ -> keep all rows not complying with the mask
    mask = ~((gdf['highway'] == 'footway') & (gdf["bicycle"] != "yes"))
    gdf_filtered = gdf[mask]

    # Filter out motorways
    mask = ~((gdf_filtered['highway'] == 'motorway') | (gdf_filtered['highway'] == 'motorway_link'))
    gdf_filtered = gdf_filtered[mask]

    # Filter out irrelevant highway types
    mask = ~((gdf_filtered['highway'] == 'bus_guideway') | 
             (gdf_filtered['highway'] == 'escape') | 
             (gdf_filtered['highway'] == 'traceway') | 
             (gdf_filtered['highway'] == 'steps') |
             (gdf_filtered['highway'] == 'corridor') | 
             (gdf_filtered['highway'] == 'via_ferrata') |
             (gdf_filtered['highway'] == 'proposed') |
             (gdf_filtered['highway'] == 'construction'))
    gdf_filtered = gdf_filtered[mask]

    return gdf_filtered

