"""
Module for computing cyclability metrics for road segments using a simple 
weighted linear model. All input factors are normalized to [0, 1].

This implementation parses segment attributes, retrieves weights and feature mapping from YAML files, and 
computes a global cyclability score.
"""

import numpy as np
from ..utils.config_reader import read_config
import geopandas as gpd
import pandas as pd

def compute_metrics_from_segment(segment: dict,
                                weights_config_path: str,
                                cyclability_config_path: str) -> float:
    """
    Compute a cyclability score for a single road segment based on YAML configurations

    Parameters
    ----------
    segment: dict
        Dictionary containing parsed segment information
    weights_config_path: str
        Path to YAML file containing feature weights
    cyclability_config_path: str
        Path to YAML file defining cyclability feature configurations

    Returns
    -------
    float
        Computed cyclability metric for the segment
    """

    #%% INGEST

    # Gather config parameters from YAML files (remove version info from resulting dict)
    weights_config = read_config('weights', weights_config_path)
    weights_config.pop('version')

    weights = weights_config['cyclability']
    cyclability_config = read_config('cyclability', cyclability_config_path)
    cyclability_config.pop('version')

    #%% COMPUTE METRICS

    metrics = 0
    all_features_metrics = {}

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
        
        all_features_metrics[feature_name] = feature_metrics


    # Compute final metrics

    ## For each weight group (cyclability, physical, traffic, regulation)
    for group_name, group_config in weights.items():
        group_weight = group_config['weight']
        group_metrics = 0.0

        # Cycle over available features for i-th group
        for feature_name, feature_weight in group_config['features'].items():
            feature_metrics = all_features_metrics[feature_name]
            
            # Compute total metrics for i-th group
            group_metrics += feature_metrics * feature_weight

        # Compounded metrics
        metrics += group_metrics * group_weight

    segment['cyclability_metrics'] = metrics

    return metrics