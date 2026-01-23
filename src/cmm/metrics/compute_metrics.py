import pandas as pd
import geopandas as gpd
from ..data.normalize.cleaning import prepare_cyclability_segment
from ..utils.config_reader import read_config
from cmm.utils.helpers import row_get, row_has, row_items
import logging
from cmm.domain.segment import Segment
from typing import Any

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_segment_for_metrics(gdf_row: Any,
                                metrics_name: str) -> Segment:
    """
    Prepare segment dataclass for a specific metrics type.

    Parameters
    ----------
    gdf_row: Any
        Row from a GeoDataFrame representing road segment (OSM data).
    metrics_name: str
        Name of metrics to consider (e.g., "cyclability").
    
    Returns
    -------
    Segment
        Segment dataclass object corresponding to specified metrics.
        For example, "cyclability" returns a CyclabilitySegment.
    """

    # Initiate Segment dataframe for cyclability
    if metrics_name == "cyclability":
        return prepare_cyclability_segment(gdf_row) # Returns a CyclabilitySegment dataclass
    else:
        raise ValueError(f"Metrics not available: {metrics_name}")

def compute_metrics_score_from_segment(segment: Segment,
                                        weights_config: dict,
                                        metrics_config: dict,
                                        metrics_name: str) -> tuple[float, dict]:
    """
    Compute metrics score for a single road segment based on YAML configurations

    Parameters
    ----------
    segment: Segment
        Segment object containing parsed segment information
    weights_config: dict
        Dict from YAML file containing feature weights
    metrics_config: dict
        Dict from YAML file defining metrics feature configurations
    metrics_name: str
        Name of metrics (e.g., cyclability) - must comply with YAML definitions
        
    Returns
    -------
    float
        Computed metrics score for the segment
    dict
        Compute metrics score components for the segment
    """

    #%% INGEST

    # Gather metrics weights from YAML files
    weights_metrics = weights_config[metrics_name]

    #%% COMPUTE METRICS SCORE

    metrics_score = 0
    all_features_scores = {}

    # Cycle each feature in YAML configuration file
    for feature_name, feature_config in metrics_config.items():
        # Define value of given feature for current segment
        feature_value = getattr(segment, feature_name)
        is_null = pd.isna(feature_value)
        # If categorical parameter type in YAML file, select feature value directly from feature_value
        if feature_config["type"] == "categorical":
            # Make feature value lower case (consistency)
            feature_value = str(feature_value).lower()
            feature_score = feature_config["mapping"].get(feature_value)    
            if feature_score is None:
                raise ValueError(
                    f"The value {repr(feature_value)} for feature '{feature_name}' "
                    f"is missing from the YAML mapping. Please add it to the 'categorical' mapping.\n"
                    f"Segment for which mapping is missing: '{segment.osm_id}'"
                )
        
        # If continuous parameter type in YAML file, get bin for which feature_value is less 
        # or equal than threshold
        elif feature_config["type"] == "continuous":
            for bin in feature_config["bins"]:
                # High maxspeed score for footway and cycleway type when no info is given (typical)
                if feature_name == "maxspeed" and is_null and (segment.highway in ("footway", "cycleway")):
                    feature_score = 1.0 
                    break
                # Assumption: assign high maxspeed score when no info is avaiable BUT bike_infrastructure is of highest quality,
                # i.e., separate from road itself.
                # bike_infrastructure is processed before maxspeed, so all_features_scores can be accessed.
                elif feature_name == "maxspeed" and is_null and all_features_scores.get("bike_infrastructure") == 1.0:
                    feature_score = 1.0
                    break
                # Conservative assumption: assign neutral maxspeed score if maxspeed is not given and segment type is legal
                elif feature_name == "maxspeed" and is_null:
                    feature_score = 0.5
                    break
                # Assign score
                elif float(feature_value) <= bin["max"]:
                    feature_score = bin["metrics"]
                    break
        
        all_features_scores[feature_name] = feature_score

    # Compute final metrics

    ## For each weight group (e.g.: cyclability, physical, traffic, regulation)
    for group_name, group_config in weights_metrics.items():
        group_weight = group_config["weight"]
        group_score = 0.0

        # Cycle over available features for i-th group
        for feature_name, feature_weight in group_config["features"].items():
            feature_score = all_features_scores[feature_name]
            
            # Compute total metrics for i-th group
            group_score += feature_score * feature_weight

        # Compounded metrics
        metrics_score += group_score * group_weight

    return metrics_score, all_features_scores

def define_segment_with_metrics_score(gdf_row: Any,
                                    weights_config: dict,
                                    metrics_config: dict,
                                    metrics_name: str) -> tuple[Segment, dict]:
    """
    Return segment augmented with selected metrics score

    Parameters
    ----------
    gdf_row: Any
        Row from GeoDataFrame representing a road segment
    weights_config: dict
        Dict from YAML file containing feature weights
    metrics_config: dict
        Dict from YAML file defining metrics feature configurations
    metrics_name: str
        Name of metrics (e.g., cyclability) - must comply with YAML definitions

    Returns
    -------
    Segment
        Segment dataclass augmented with metrics score
    dict
        Dictionary storing segment metrics scores for each feature 
    """

    # Initiate Segment dataclass for given gdf row and specific metric
    # (for metrics_name = "cyclability" -> CyclabilitySegment dataclass -- see dataclass structure in cmm/domain/segment)
    segment = prepare_segment_for_metrics(gdf_row, metrics_name)

    # Compute metrics score based on YAML configs
    metrics_score, metrics_features_scores = compute_metrics_score_from_segment(segment, weights_config, metrics_config, metrics_name)
    
    # Augment segment dataclass with metrics score (use dataclass method set_metrics)
    segment.set_metrics(metrics_name, metrics_score)

    return segment, metrics_features_scores

def define_augmented_geodataframe(gdf: gpd.GeoDataFrame,
                                weights_config: dict,
                                metrics_config: dict) -> tuple[gpd.GeoDataFrame, list]:
    """
    Return GeoDataFrame augmented with metrics scores for all segments and list of metrics features scores.

    For now only cyclability metrics is considered

    Parameters
    ----------
    gdf: gpd.GeoDataFrame
        GeoDataFrame containing road segments
    weights_config: dict
        Dict from YAML file containing feature weights
    metrics_config: dict
        Dict from YAML file defining metrics feature configurations
        
    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame with segments augmented by metrics scores
    list
        List of metrics scores of all features for all segments
    """

    total = len(gdf)

    # Initiate cyclability results list
    segments_with_components_cyclability = []

    # Cyclability - Define segments augmented with metrics scores
    for idx, gdf_row in enumerate(gdf.itertuples(index=False), start = 1):
        
        # Compute segment augmented with metrics (and metric components) for this row
        segments_with_components_cyclability.append(
            define_segment_with_metrics_score(gdf_row, weights_config, metrics_config, "cyclability")
        )

        # Logging of progress every 100 rows or last row
        if idx % 100 == 0 or idx == total:
            logger.info(f"Processed {idx}/{total} segments.")

    # Cyclability - Unpack segments and associated score features informaton
    segments_cyclability = []
    metrics_features_scores_cyclability = []
    
    for seg, feats in segments_with_components_cyclability:
        segments_cyclability.append(seg)
        metrics_features_scores_cyclability.append(feats)



    # Define final GDF (only cyclability available)
    # Pandas automatically converts dataclasses fields to columns - no need to convert manually
    gdf_final = gpd.GeoDataFrame(segments_cyclability, crs = gdf.crs)
    
    return gdf_final, metrics_features_scores_cyclability

def compute_total_city_metrics(gdf: gpd.GeoDataFrame) -> tuple[float, dict]:
    """
    Compute the overall city score and the percentage of missing features in GeoDataFrame.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        GeoDataFrame containing city network segments with at least:
        - segment_length: length of each segment
        - total_score: score of each segment
        - missing_info: dict indicating missing features for the segment

    Returns
    -------
    total_city_score : float
        The weighted average score of the city, normalized by total network length.
    city_missing_features : dict
        A dictionary showing the percentage of segments missing each feature 
        (i.e., 'maxspeed', 'surface', 'lighting').
    """

    # Initialize variables
    total_city_score = 0.0
    city_missing_features = {
        "maxspeed": 0.0,
        "surface": 0.0,
        "lighting": 0.0
    }

    # Define total network segments length
    total_network_length = gdf["segment_length"].sum()
    # Total number of segments
    n_segments = gdf.shape[0]

    for row in gdf.itertuples(index = False):
        
        length = row_get(row, "segment_length")
        score = row_get(row, "total_score")
        missing_info = row_get(row, "missing_info")

        # Get partially normalized score
        total_city_score += score * length

        # Count missing data in dedicated dict
        for feature in city_missing_features:
            if missing_info.get(feature):
                city_missing_features[feature] += 1

    # Divide by total amount of segments
    city_missing_features = {
        idx: val / n_segments for  idx, val in city_missing_features.items() 
    }        

    # Normalize by total network segment length
    total_city_score = total_city_score / total_network_length

    print(f"total_length: {total_network_length}")
    print(f"Total rows: {n_segments}")

    return total_city_score, city_missing_features