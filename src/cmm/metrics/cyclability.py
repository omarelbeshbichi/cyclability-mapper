"""
Module used to implement a simple weighted linear model for computing a cyclability metrics
for a road segment. For now, all factors are assumed to be already normalized to [0, 1].

Initial placeholder implementation used to further test/validate the package environment.
"""

import numpy as np
from ..utils.config_reader import read_config
import geopandas as gpd
import pandas as pd

def extract_all_cycleway_tags(gdf_row: pd.Series) -> dict:
    """Extract all cycleway-related data from GeoDataFrame row and store them in dictionary"""

    return {
        key: val for key, val in gdf_row.items()
        if isinstance(val, str) and 'cycleway' in key and pd.notna(val)
    }


def init_normal_cycleway_info() -> dict:
    """Initialize normalized cycleway dictionary"""

    return {
        'left': {},
        'right': {},
        'undefined': {}
    }


def normalize_cycleway_info(tags: dict) -> dict:
    """Normalize cycleway information into a dictionary"""

    cycleway_dict = init_normal_cycleway_info()

    for key, val in tags.items():
        
        # 1) unpack key
        keys_split = key.split(':') # 'cycleway:left' -> ['cycleway', 'left']

        # 2) cycleway = lane
        if len(keys_split) == 1:
            cycleway_dict['undefined']['type'] = val
            continue

        # 3) cycleway:left = lane | cycleway:left:oneway = -1 | longer
        side = keys_split[1]

        ## define param depending on type
        if len(keys_split) == 2:
            param = 'type'
            if side not in ['left', 'right', 'both']:
                continue

        if len(keys_split) > 2:
            param = ':'.join(keys_split[2:]) # cycleway:left:oneway -> oneway
            if side not in ['left', 'right', 'both']:
                continue
        
        # Handle type 'both' into 'left' and 'right'
        features = ('left', 'right') if side == 'both' else (side,)

        # Populate dictionary
        for feature in features:
            cycleway_dict[feature][param] =  val
    
    return cycleway_dict


def compute_cyclability_metrics(gdf_row: pd.Series) -> float:
    """
    Compute cyclability metrics of road segment as weighted sum of five normalized 
    parameters describing cycling quality.

    Parameters
    ----------
    gdf_row: pd.Series
        A single row of the GeoDataFrame representing a road segment.

    Returns
    -------
    float
        Cyclability metrics computed as dot product of input paramters and associated weights
    """

    # Gather config parameters from YAML files
    weights_config = read_config('weights')
    weights = weights_config['cyclability']
    cyclability_config = read_config('cyclability')

    # Gather quality factors
    lit = gdf_row['lit']
    highway = gdf_row['highway']
    maxspeed = gdf_row['maxspeed']
    surface = gdf_row['surface']
    
    # Gather cycleway info
    cycleway_tags = extract_all_cycleway_tags(gdf_row)
    cycleway_dict = normalize_cycleway_info(cycleway_tags)
    print(cycleway_dict)
    
    #factors = np.array([
    #    bike_infrastructure, 
    #    slope_factor, 
    #    speed_factor, 
    #    surface_quality, 
    #    lighting
    #])
    
    #cyclability_metrics = np.dot(weights, factors)

    return 1.0