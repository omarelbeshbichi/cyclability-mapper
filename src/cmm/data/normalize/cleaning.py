"""
Module providing functions to normalize OSM data.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from cmm.domain.segment import CyclabilitySegment

def parse_maxspeed_to_kmh(value):
    """
    Convert OSM maxspeed value to km/h.
    """
    
    if value == None:
        return None

    # Return value itself if present
    if isinstance(value, (int, float)):
        return int(value)

    # Normalize string for processing
    value = value.lower().strip()

    # Convert mph to km/h
    if "mph" in value:
        maxspeed_mph = value.split()[0]
        return int( int(maxspeed_mph) * 1.60934 )
    
    # Convert knots to km/h (irrelevant but added nonetheless)
    if "knots" in value:
        maxspeed_knots = value.split()[0]
        return int( float(maxspeed_knots) * 1.852 )

    # If digit return value itself
    if value.isdigit():
        return int(value)
    
    # Else...
    return None

def normalize_maxspeed_info(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Normalize maxspeed column of GeoDataFrame to km/h.
    """
    
    gdf = gdf.copy()

    # Update maxspeed info with normalized data (replace for now)
    gdf["maxspeed"] = gdf["maxspeed"].apply(parse_maxspeed_to_kmh)
    
    # Convert updated values as strings and use None for NaN - comply with pipeline
    gdf["maxspeed"] = [
        str(int(val)) if not pd.isna(val) else None 
        for val in gdf["maxspeed"]
    ]

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

    # Filter out all segments with bicycle restriction
    # ~ -> keep all rows not complying with the mask
    mask = ~(gdf["bicycle"] == "no")
    gdf_filtered = gdf[mask]

    # Filter out all highway = footway LineStrings with no bicycle designation
    # ~ -> keep all rows not complying with the mask
    mask = ~((gdf_filtered["highway"] == "footway") & (gdf_filtered["bicycle"] != "yes"))
    gdf_filtered = gdf_filtered[mask]

    # Filter out all highway = pedestrian LineStrings with no bicycle designation
    # ~ -> keep all rows not complying with the mask
    mask = ~((gdf_filtered["highway"] == "pedestrian") & (gdf_filtered["bicycle"] != "yes"))
    gdf_filtered = gdf_filtered[mask]

    # Filter out motorways
    mask = ~((gdf_filtered["highway"] == "motorway") | (gdf_filtered["highway"] == "motorway_link"))
    gdf_filtered = gdf_filtered[mask]

    # Filter out irrelevant highway types
    mask = ~((gdf_filtered["highway"] == "bus_guideway") | 
            (gdf_filtered["highway"] == "escape") | 
            (gdf_filtered["highway"] == "traceway") | 
            (gdf_filtered["highway"] == "steps") |
            (gdf_filtered["highway"] == "corridor") | 
            (gdf_filtered["highway"] == "via_ferrata") |
            (gdf_filtered["highway"] == "proposed") |
            (gdf_filtered["highway"] == "construction") |
            (gdf_filtered["highway"] == "service") |
            (gdf_filtered["highway"] == "elevator") |
            (gdf_filtered["highway"] == "platform") |
            (gdf_filtered["highway"] == "track") |
            (gdf_filtered["highway"] == "path") |
            (gdf_filtered["highway"] == "trunk") | # assuming trunks are mostly not cyclable
            (gdf_filtered["highway"] == "trunk_link"))
            

    gdf_filtered = gdf_filtered[mask]

    return gdf_filtered

def extract_all_cycleway_tags(gdf_row: pd.Series) -> dict:
    """Extract all cycleway-related data from GeoDataFrame row and store them in dictionary"""

    return {
        key: val for key, val in gdf_row.items()
        if isinstance(val, str) and "cycleway" in key and pd.notna(val)
    }

def extract_all_oneway_tags(gdf_row: pd.Series) -> dict:
    """Extract all oneway-related data from GeoDataFrame row and store them in dictionary"""

    return {
        key: val for key, val in gdf_row.items()
        if isinstance(val, str) and "oneway" in key and "cycleway" not in key and pd.notna(val)
    }

def init_normal_cycleway_info() -> dict:
    """Initialize normalized cycleway dictionary"""

    return {
        "left": {},
        "right": {},
        "undefined": {}
    }

def normalize_cycleway_info(tags: dict) -> dict:
    """Normalize cycleway information into a dictionary"""

    cycleway_dict = init_normal_cycleway_info()

    for key, val in tags.items():
        
        # 1) unpack key
        keys_split = key.split(":") # "cycleway:left" -> ["cycleway", "left"]

        # 2) cycleway = lane
        if len(keys_split) == 1:
            cycleway_dict["undefined"]["type"] = val
            continue

        # 3) cycleway:left = lane | cycleway:left:oneway = -1 | longer
        side = keys_split[1]

        ## define param depending on type
        if len(keys_split) == 2:
            param = "type"
            if side not in ["left", "right", "both"]: # consider here type "both" although rarely used in API
                continue

        if len(keys_split) > 2:
            param = ":".join(keys_split[2:]) # cycleway:left:oneway -> oneway
            if side not in ["left", "right", "both"]:
                continue
        
        # Handle type "both" into "left" and "right"
        features = ("left", "right") if side == "both" else (side,)

        # Populate dictionary
        for feature in features:
            cycleway_dict[feature][param] =  val
    
    return cycleway_dict

def prepare_cyclability_segment(gdf_row: pd.Series) -> CyclabilitySegment:
    """
    Prepare dictionary of cyclability features from a single GeoDataFrame row.

    Parameters
    ----------
    gdf_row: pd.Series
        Row from GeoDataFrame representing a road segment, containing 
        required attributes.

    Returns
    -------
    CyclabilitySegment
        CyclabilitySegment dataclass with parsed cyclability information:
        - "id": segment identifier
        - "name": segment name
        - "geometry": segment geometry
        - "bike_infrastructure": type of cycling infrastructure
        - "oneway": "yes" if one-way for bikes, "no" otherwise
        - "maxspeed": maximum speed allowed
        - "surface": surface type
        - "lighting": lighting condition
        - "highway": highway type
    """


    #%% INIT 
    # Gather segments facts
    osm_id =  gdf_row.get("osm_id")
    name =  gdf_row.get("name")
    geometry = gdf_row.get("geometry")
    segment_length = gdf_row.get("segment_length")

    # Gather quality factors
    lit = gdf_row.get("lit")
    highway = gdf_row.get("highway")
    maxspeed = gdf_row.get("maxspeed")
    surface = gdf_row.get("surface") or "unknown" # Fallback to "unknown" if None
    
    # Gather cycleway info
    cycleway_tags = extract_all_cycleway_tags(gdf_row)
    cycleway_dict = normalize_cycleway_info(cycleway_tags)
    
    # Gather oneway info
    oneway_dict = extract_all_oneway_tags(gdf_row)

    ## Handle lighting information
    if lit == None:
        lit = "unknown"
    if lit == "24/7":
        lit = "yes"
    if lit == "disused":
        lit = "no"
    if lit == "yes;no":
        lit = "yes"
   
    # Initialize parameters
    bike_ways = "both"
    bike_infra = "none"

    #%% PARSE

    # Parse oneway information
        # In OSM "oneway=yes" indicates a one-way cycleway
        # see: https://wiki.openstreetmap.org/wiki/Key:oneway:bicycle 
    if oneway_dict.get("oneway") == "yes" and "oneway:bicycle" not in oneway_dict:
        bike_ways = "one"
    elif oneway_dict.get("oneway") == "yes" and oneway_dict.get("oneway:bicycle") == "no":
        bike_ways = "both"

    # Extract normalization type (from normalize_cycleway_info) - if not available use None
    left_type = cycleway_dict["left"].get("type") if cycleway_dict["left"] else None
    right_type = cycleway_dict["right"].get("type") if cycleway_dict["right"] else None
    undefined_type = cycleway_dict["undefined"].get("type") if cycleway_dict["undefined"] else None

    # Parse cycleway_dict

    ## Define cycleways and cyclable footways
    # In footways and cycleways I don't apply maxspeed penalty
    if highway == "footway":
        bike_infra = "footway"
        maxspeed = None
    elif highway == "cycleway":
        bike_infra = "cycleway"
        maxspeed = None
    ## Both-sides cycleway
    elif left_type and right_type:
        bike_infra = left_type  # arbitrary, symmetric assumption
    ## Generic cycleway info & both sides
    elif undefined_type:
        bike_infra = undefined_type
    ## Left cycleway
    elif left_type:
        bike_infra = left_type
    ## Right cycleway
    elif right_type:
        bike_infra = right_type
    else:
        bike_infra = "none"

    # Final adjustments
    if bike_infra == "no":
        bike_infra = "none"  

    ## If data present in gdf, load them instead of parsing
    # This section is used when loading data from PostGIS (jobs/recompute_metrics)
    if "bike_infra" in gdf_row and pd.notna(gdf_row["bike_infra"]):
        bike_infra = gdf_row["bike_infra"]
        bike_ways = gdf_row["is_oneway"]
        
    ## Store key information in Segment dataclass
    return CyclabilitySegment(
        osm_id = osm_id,
        name = name,
        geometry = geometry,
        segment_length = segment_length,
        bike_infrastructure = bike_infra,
        oneway = "yes" if bike_ways == "one" else "no",
        maxspeed = maxspeed,
        surface = surface,
        lighting = lit,
        highway = highway
    )