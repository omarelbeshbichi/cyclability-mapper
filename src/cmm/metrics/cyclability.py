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
            if side not in ['left', 'right', 'both']: # consider here type 'both' although rarely used in API
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
    #%% INGEST
    # Gather config parameters from YAML files
    weights_config = read_config('weights')
    weights = weights_config['cyclability']
    cyclability_config = read_config('cyclability')

    # Gather quality factors
    lit = gdf_row.get('lit')
    highway = gdf_row.get('highway')
    maxspeed = gdf_row.get('maxspeed')
    surface = gdf_row.get('surface') or 'unknown' # Fallback to 'unknown' if None
    
    # Gather cycleway info
    cycleway_tags = extract_all_cycleway_tags(gdf_row)
    cycleway_dict = normalize_cycleway_info(cycleway_tags)
    
    ## Handle lack of information
    if lit == None:
        lit = 'unknown'

    print(cycleway_dict)
    
    #%% INIT + PARSE

    # Initialize parameters
    bike_ways = 'none'
    bike_infra = 'none'

    # Parse cycleway_dict

    ## Cyclable footways
    if highway == 'footway':
        bike_infra = 'footway'
        bike_ways = 'both'
        maxspeed = 30

    ## Both-sides cycleway
    if (cycleway_dict['left'] and cycleway_dict['right']):
        # assuming at this stage left/right symmetrical properties
        # using properties of left side - arbitrary
        bike_infra = cycleway_dict['left']['type'] 
        bike_ways = 'both'

    ## Generic cycleway info & both sides
    elif cycleway_dict['undefined']:   
        bike_infra = cycleway_dict['undefined']['type']
        bike_ways = 'both'

    ## Left cycleway
    elif cycleway_dict['left'] and not (cycleway_dict['undefined'] or cycleway_dict['right']): 
        bike_infra = cycleway_dict['left']['type']
        
        # Check way
        if 'oneway' in cycleway_dict['left']:
            # In OSM 'oneway=no' indicates a bidirectional cycleway
            # see: https://wiki.openstreetmap.org/wiki/Key:oneway:bicycle 
            if cycleway_dict['left']['oneway'] == 'no':
                bike_ways = 'both'
            else:
                bike_ways = 'one'
        else:
            bike_ways = 'one'

    ## Right cycleway   
    elif cycleway_dict['right'] and not (cycleway_dict['undefined'] or cycleway_dict['left']): 
        bike_infra = cycleway_dict['right']['type']
        
        # Check way
        if 'oneway' in cycleway_dict['right']:
            # Equivalent to left case
            if cycleway_dict['right']['oneway'] == 'no':
                bike_ways = 'both'
            else:
                bike_ways = 'one'
        else:
            bike_ways = 'one'


    ## Store key information in segment dictionary
    segment = {
        'bike_infrastructure': bike_infra,
        'bike_ways': bike_ways,
        'maxspeed': maxspeed,
        'surface': surface,
        'lighting': lit,
        'highway': highway
    }

    print(segment)

    #%% COMPUTE METRICS

    metrics = 0
    # Cycle each feature in YAML configuration file
    for feature_name, feature_config in cyclability_config.items():
        # Define value of given feature for current segment
        current_value = segment.get(feature_name)
        # If categorical parameter type in YAML file, select matrics value directly from current_value
        if feature_config["type"] == "categorical":
            feature_metrics = feature_config["mapping"].get(current_value)    
            if feature_metrics is None:
                raise ValueError(
                    f"The value {repr(current_value)} for feature '{feature_name}' "
                    f"is missing from the YAML mapping. Please add it to the 'categorical' mapping."
                )
            



        # If continuous parameter type in YAML file, get bin for which current_value is less 
        # or equal than threshold
        elif feature_config["type"] == "continuous":
            for bin in feature_config["bins"]:
                if float(current_value) <= bin["max"]:
                    feature_metrics = bin["metrics"]
                    break

        # Linearly combine weights from all features
        metrics += feature_metrics * weights[feature_name]

    print(metrics)

    return 1.0