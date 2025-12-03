"""
Module used to implement a simple weighted linear model for computing a cyclability score
for a road segment. For now, all factors are assumed to be already normalized to [0, 1].

Initial placeholder implementation used to further test/validate the package environment.
"""

import numpy as np

def compute_cyclability_score(bike_infrastructure: float, 
                              slope_factor: float, 
                              speed_factor: float, 
                              surface_quality: float, 
                              lighting: float ) -> float:
    """
    Compute cyclability score of road segment as weighted sum of five normalized 
    parameters describing cycling quality.

    Parameters
    ----------
    bike_infrastructure: float
        Normalized parameter for bike infrastructure quality
    slope_factor: float
        Normalized parameter for slope
    speed_factor: float
        Normalized parameter for maximum speed
    surface_quality: float
        Normalized parameter for surface quality
    lighting: float
        Normalized lighting parameter

    Returns
    -------
    float
        Cyclability score computed as dot product of input paramters and associated weights
    """

    weights = np.array([0.3, 0.2, 0.2, 0.2, 0.1])

    factors = np.array([
        bike_infrastructure, 
        slope_factor, 
        speed_factor, 
        surface_quality, 
        lighting
    ])
    
    cyclability_score = np.dot(weights, factors)

    return cyclability_score