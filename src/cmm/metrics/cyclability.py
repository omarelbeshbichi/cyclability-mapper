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

