import pandas as pd
import geopandas as gpd
from cmm.data.normalize.cleaning import prepare_cyclability_segment
from cmm.utils.config_helpers import read_config, add_config_data
from cmm.utils.helpers import row_get, row_has, row_items
import logging
from cmm.domain.segment import Segment
from typing import Any
from pathlib import Path

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_segment_for_metrics(gdf_row: Any,
                                metrics_name: str,
                                excellent_bike_infra: dict) -> Segment:
    """
    Prepare segment dataclass for a specific metrics type.

    Parameters
    ----------
    gdf_row: Any
        Row from a GeoDataFrame representing road segment (OSM data).
    metrics_name: str
        Name of metrics to consider (e.g., "cyclability").
    excellent_bike_infra: dict
        Dict from YAML file defining bike_infrastructure metrics features from YAML file for which score is 1.0
    
    Returns
    -------
    Segment
        Segment dataclass object corresponding to specified metrics.
        For example, "cyclability" returns a CyclabilitySegment.
    """

    # Initiate Segment dataframe for cyclability
    if metrics_name == "cyclability":
        return prepare_cyclability_segment(gdf_row, excellent_bike_infra) # Returns a CyclabilitySegment dataclass
    else:
        raise ValueError(f"Metrics not available: {metrics_name}")

def compute_metrics_score_from_segment(segment: Segment,
                                        weights_config: dict,
                                        metrics_config: dict,
                                        metrics_config_path: str,
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
    metrics_config_path: str
        Path of YAML file defining metrics feature configurations
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
                
                logging.warning(f"The value {repr(feature_value)} for feature '{feature_name}' "
                    f"is missing from the YAML mapping. Please add it to the 'categorical' mapping.\n"
                    f"Segment for which mapping is missing: '{segment.osm_id}'")
                
                feature_score = float(input(
                    f"Enter score for {repr(feature_value)} for feature '{feature_name}': "
                    ))
                
                # Save to YAML
                add_config_data(feature_name, feature_value, feature_score, metrics_config_path)
                
                # Update feature_config dict for current loop
                feature_config["mapping"][feature_value] = feature_score       

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
                    feature_score = feature_config["fallback"]
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
                                    metrics_config_path: str,
                                    excellent_bike_infra: dict,
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
    metrics_config_path: str
        Path of YAML file defining metrics feature configurations
    excellent_bike_infra: dict
        Dict from YAML file defining bike_infrastructure metrics features from YAML file for which score is 1.0
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
    segment = prepare_segment_for_metrics(gdf_row, metrics_name, excellent_bike_infra)

    # Compute metrics score based on YAML configs
    metrics_score, metrics_features_scores = compute_metrics_score_from_segment(segment, 
                                                                                weights_config, 
                                                                                metrics_config,
                                                                                metrics_config_path,
                                                                                metrics_name)
    
    # Augment segment dataclass with metrics score (use dataclass method set_metrics)
    segment.set_metrics(metrics_name, metrics_score)

    return segment, metrics_features_scores

def define_augmented_geodataframe(gdf: gpd.GeoDataFrame,
                                weights_config: dict,
                                metrics_config: dict,
                                metrics_config_path: str,
                                excellent_bike_infra: dict) -> tuple[gpd.GeoDataFrame, list]:
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
    metrics_config_path: str
        Path of YAML file defining metrics feature configurations 
    excellent_bike_infra: dict
        Dict from YAML file defining bike_infrastructure metrics features from YAML file for which score is 1.0

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
            define_segment_with_metrics_score(gdf_row, 
                                              weights_config, 
                                              metrics_config,
                                              metrics_config_path,
                                              excellent_bike_infra, 
                                              "cyclability")
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

def compute_total_city_metrics(gdf: gpd.GeoDataFrame,
                               metrics_name: str,
                               weights_config_path: Path) -> tuple[float, dict, float]:
    """
    Compute the overall city score and the percentage of missing features in GeoDataFrame.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        GeoDataFrame containing city network segments with at least:
        - segment_length: length of each segment
        - total_score: score of each segment
        - missing_info: dict indicating missing features for the segment
    metrics_name: str
        Metrics name (e.g., "cyclability")
    weights_config_path: Path
        Path of weights configuration file.
    Returns
    -------
    total_city_score : float
        The weighted average score of the city, normalized by total network length.
    feature_uncertainty_contributions : dict
        Per-feature contribution to metric uncertainty
    total_city_score_uncertainty: float
        Total metric uncertainty
    """

    # Get config info
    #(remove version info from resulting dict)
    weights_config = read_config("weights", "yaml", weights_config_path)
    weights_config.pop("version")
    weights_metrics = weights_config[metrics_name]

    # Initialize variables
    total_city_score = 0.0
    feature_uncertainty_contributions = {
        "maxspeed": 0.0,
        "surface": 0.0,
        "lighting": 0.0
    }

    # Define total network segments length
    total_network_length = gdf["segment_length"].sum()

    for row in gdf.itertuples(index = False):
        
        length = row_get(row, "segment_length")
        score = row_get(row, "total_score")
        missing_info = row_get(row, "missing_info")

        # Get partially normalized score
        total_city_score += score * length

        # Get uncertainty data by counting lengths of segments that do not have info in dedicated dict
        for feature in feature_uncertainty_contributions:
            if missing_info.get(feature):
                feature_uncertainty_contributions[feature] += length

    # Divide by total length of segments
    total_city_score = total_city_score / total_network_length

    feature_uncertainty_contributions = {
        idx: val / total_network_length for  idx, val in feature_uncertainty_contributions.items() 
    }        

    # Apply weight to uncertainty
    feature_weight_total = {
        "maxspeed": 0.0,
        "surface": 0.0,
        "lighting": 0.0
    }
    # Cycle over all features considered in feature_uncertainty_contributions
    for feature in feature_uncertainty_contributions:
        # Cycle over all parts of weight YAML
        for group_config in weights_metrics.values():            
            # Store group weight
            group_weight = group_config["weight"]
            # Cycle over features for i-th group
            for feature_name, rel_weight in group_config["features"].items():
                # Collect info only if given feature is found
                if feature_name == feature:
                    feature_weight_total[feature] = rel_weight * group_weight

    all_scores = pd.Series(feature_uncertainty_contributions)
    all_weights = pd.Series(feature_weight_total)

    feature_uncertainty_contributions = all_scores * all_weights

    total_city_score_uncertainty = feature_uncertainty_contributions.sum()

    return total_city_score, feature_uncertainty_contributions, total_city_score_uncertainty