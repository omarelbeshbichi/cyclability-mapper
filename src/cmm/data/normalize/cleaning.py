"""
Module providing functions to normalize OSM data.
"""

import geopandas as gpd
import pandas as pd
import numpy as np


def parse_maxspeed_to_kmh(value):
    """
    Convert OSM maxspeed value to km/h.
    """
        
    # Return NaN if None
    if value is None:
        return np.nan

    # Return value itself if present
    if isinstance(value, (int, float)):
        return int(value)

    # Normalize string for processing
    value = value.lower().strip()

    # Convert mph to km/h
    if 'mph' in value:
        maxspeed_mph = value.split()[0]
        return int( int(maxspeed_mph) * 1.60934 )
    
    # Convert knots to km/h
    if 'knots' in value:
        maxspeed_knots = value.split()[0]
        return int( float(maxspeed_knots) * 1.852 )

    # If digit return value itself
    if value.isdigit():
        return int(value)
    
    # Else...
    return np.nan


def normalize_maxspeed_info(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Normalize maxspeed column of GeoDataFrame to km/h.
    """
    
    gdf = gdf.copy()

    # Update maxspeed info with normalized data (replace for now)
    gdf["maxspeed"] = gdf["maxspeed"].apply(parse_maxspeed_to_kmh)

    return gdf


def restrict_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
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

    # Filter out redundant and unnecessary features
    # (placeholder filter)
    gdf_filtered.drop(columns='@id', inplace=True)
    gdf_filtered.drop(columns='wikidata', inplace=True)
    gdf_filtered.drop(columns='smoothness', inplace=True)
    gdf_filtered.drop(columns='crossing', inplace=True)

    return gdf_filtered

def extract_all_cycleway_tags(gdf_row: pd.Series) -> dict:
    """Extract all cycleway-related data from GeoDataFrame row and store them in dictionary"""

    return {
        key: val for key, val in gdf_row.items()
        if isinstance(val, str) and 'cycleway' in key and pd.notna(val)
    }

def extract_all_oneway_tags(gdf_row: pd.Series) -> dict:
    """Extract all oneway-related data from GeoDataFrame row and store them in dictionary"""

    return {
        key: val for key, val in gdf_row.items()
        if isinstance(val, str) and 'oneway' in key and 'cycleway' not in key and pd.notna(val)
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

def prepare_cyclability_segment(gdf_row: pd.Series) -> dict:
    """
    Prepare dictionary of cyclability features from a single GeoDataFrame row.

    Parameters
    ----------
    gdf_row: pd.Series
        Row from GeoDataFrame representing a road segment, containing 
        required attributes.

    Returns
    -------
    dict
        Dictionary with parsed cyclability information:
        - 'id': segment identifier
        - 'name': segment name
        - 'geometry': segment geometry
        - 'bike_infrastructure': type of cycling infrastructure
        - 'oneway': 'yes' if one-way for bikes, 'no' otherwise
        - 'maxspeed': maximum speed allowed
        - 'surface': surface type
        - 'lighting': lighting condition
        - 'highway': highway type
    """


    #%% INIT 
    # Gather segments facts
    id =  gdf_row.get('id')
    name =  gdf_row.get('name')
    geometry = gdf_row.get('geometry')
    
    # Gather quality factors
    lit = gdf_row.get('lit')
    highway = gdf_row.get('highway')
    maxspeed = gdf_row.get('maxspeed')
    surface = gdf_row.get('surface') or 'unknown' # Fallback to 'unknown' if None
    
    # Gather cycleway info
    cycleway_tags = extract_all_cycleway_tags(gdf_row)
    cycleway_dict = normalize_cycleway_info(cycleway_tags)
    
    # Gather oneway info
    oneway_dict = extract_all_oneway_tags(gdf_row)

    ## Handle lack of information
    if lit == None:
        lit = 'unknown'
   
    # Initialize parameters
    bike_ways = 'both'
    bike_infra = 'none'

    #%% PARSE

    # Parse oneway information
    if oneway_dict.get('oneway') == 'yes' and 'oneway:bicycle' not in oneway_dict:
        bike_ways = 'one'
    elif oneway_dict.get('oneway') == 'yes' and oneway_dict.get('oneway:bicycle') == 'no':
        bike_ways = 'both'

    # Parse cycleway_dict

    ## Cyclable footways
    if highway == 'footway':
        bike_infra = 'footway'
        maxspeed = 30

    ## Both-sides cycleway
    if (cycleway_dict['left'] and cycleway_dict['right']):
        # assuming at this stage left/right symmetrical properties
        # using properties of left side - arbitrary
        bike_infra = cycleway_dict['left']['type'] 

    ## Generic cycleway info & both sides
    elif cycleway_dict['undefined']:   
        bike_infra = cycleway_dict['undefined']['type']

    ## Left cycleway
    elif cycleway_dict['left'] and not (cycleway_dict['undefined'] or cycleway_dict['right']): 
        bike_infra = cycleway_dict['left']['type']
        
        # Check way
        if 'oneway' in cycleway_dict['left']:
            # In OSM 'oneway=yes' indicates a one-way cycleway
            # see: https://wiki.openstreetmap.org/wiki/Key:oneway:bicycle 
            if cycleway_dict['left']['oneway'] == 'yes':
                bike_ways = 'one'

    ## Right cycleway   
    elif cycleway_dict['right'] and not (cycleway_dict['undefined'] or cycleway_dict['left']): 
        bike_infra = cycleway_dict['right']['type']
        
        # Check way
        if 'oneway' in cycleway_dict['right']:
            # Equivalent to left case
            if cycleway_dict['right']['oneway'] == 'yes':
                bike_ways = 'one'


    ## Store key information in segment dictionary
    segment = {
        'id': id,
        'name': name,
        'geometry': geometry,
        'bike_infrastructure': bike_infra,
        'oneway': 'yes' if bike_ways == 'one' else 'no',
        'maxspeed': maxspeed,
        'surface': surface,
        'lighting': lit,
        'highway': highway
    }

    return segment