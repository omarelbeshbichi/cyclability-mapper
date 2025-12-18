"""
Module used to implement a simple weighted linear model for computing a cyclability metrics
for a road segment. For now, all factors are assumed to be already normalized to [0, 1].

Initial placeholder implementation used to further test/validate the package environment.
"""

import numpy as np
from ..utils.config_reader import read_config
import geopandas as gpd

def compute_cyclability_metrics(feature) -> float:
    """
    Compute cyclability metrics of road segment as weighted sum of five normalized 
    parameters describing cycling quality.

    Parameters
    ----------
    feature:


    Returns
    -------
    float
        Cyclability metrics computed as dot product of input paramters and associated weights
    """

    # Gather config parameters
    weights_config = read_config('weights')
    weights = weights_config['cyclability']

    cyclability_config = read_config('cyclability')

    # Gather quality factors
    #feature_properties = feature['properties']

    #factors = np.array([
    #    bike_infrastructure, 
    #    slope_factor, 
    #    speed_factor, 
    #    surface_quality, 
    #    lighting
    #])
    
    #cyclability_metrics = np.dot(weights, factors)

    return 1.0