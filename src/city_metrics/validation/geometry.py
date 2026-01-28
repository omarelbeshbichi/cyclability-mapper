"""
Module for validating geometries in PostGIS database.
"""
import geopandas as gpd

def validate_gdf_linestrings(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Perform preliminary checks on GeoDataFrame LineStrings and filter out
    invalid features. 
    
    Parameters
    ----------
    gdf: gpd.GeoDataFrame
        GeoPandas GeoDataFrame.
    Returns
    -------
    gdf: gpd.GeoDataFrame
        Cleaned GeoPandas GeoDataFrame.
    """

    # Retain only LineStrings
    gdf = gdf[gdf.geometry.type == "LineString"]
    # Retain only valid features with geometry
    gdf = gdf[gdf.geometry.notnull()]
    # Retain only valid geometries
    gdf = gdf[gdf.geometry.is_valid]

    # Retain only LineStrings with valid length
    # If data is in degrees, project data into meters before calculating length (utm is in meters)
    if gdf.crs and gdf.crs.is_geographic:
        temp_gdf = gdf.to_crs(gdf.estimate_utm_crs())
        gdf = gdf[temp_gdf.geometry.length > 0]
    else:
        gdf = gdf[gdf.geometry.length > 0]

    return gdf