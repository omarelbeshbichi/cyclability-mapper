from .cyclability import compute_metrics_from_segment
import pandas as pd
import geopandas as gpd
from ..data.normalize.cleaning import prepare_cyclability_segment



def compute_cyclability_metrics(row: pd.Series,
                                weights_config_path,
                                cyclability_config_path) -> dict:
    """
    Compute cyclability metrics for single road segment

    Parameters
    ----------
    row: pd.Series
        Row from GeoDataFrame representing a road segment
    weights_config_path: str
        Path to YAML file containing feature weights
    cyclability_config_path: str
        Path to YAML file defining cyclability feature configurations

    Returns
    -------
    dict
        Segment dictionary augmented with 'cyclability_metrics'
    """

    # Normalize and parse cycleway information
    segment = prepare_cyclability_segment(row)

    # Compute metrics based on YAML configs
    metrics = compute_metrics_from_segment(segment, weights_config_path, cyclability_config_path)
    
    segment['cyclability_metrics'] = metrics

    return segment


def compute_metrics(gdf: gpd.GeoDataFrame,
                    weights_config_path,
                    cyclability_config_path) -> gpd.GeoDataFrame:
    """
    Compute cyclability metrics for all segments in a GeoDataFrame

    Parameters
    ----------
    gdf: gpd.GeoDataFrame
        GeoDataFrame containing road segments
    weights_config_path: str
        Path to YAML file containing feature weights
    cyclability_config_path: str
        Path to YAML file defining cyclability feature configurations

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame with segments augmented by cyclability metrics
    """

    # Compute cyclability metrics for all segments
    segments = [compute_cyclability_metrics(row, weights_config_path, cyclability_config_path) for _, row in gdf.iterrows()]
    
    # Define final GDF
    gdf_final = gpd.GeoDataFrame(segments, crs=gdf.crs)
    
    return gdf_final