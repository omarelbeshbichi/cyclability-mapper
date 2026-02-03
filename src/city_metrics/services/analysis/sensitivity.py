from pathlib import Path
import logging 
from city_metrics.services.metrics.loader import load_segments_for_metrics_recompute
from city_metrics.utils.config_helpers import read_config
from city_metrics.data.export.postgres import dataframe_to_postgres
from city_metrics.data.export.postgres import prepare_group_sweep_city_metrics_df_for_postgis
from city_metrics.data.export.postgres import delete_city_rows
from city_metrics.analysis.sensitivity import sweep_group_weight

def sensitivity_single_weight_sweep(city_name: str,
                                    target_group: str, 
                                    delta_range: float,
                                    weights_config_path: Path,
                                    metrics_config_path: Path,
                                    upload: bool = True) -> None:
    """
    Perform sweep sensitivity analysis on group weights employed for given city.
    This analysis is diagnostic only - it provides idea of whether city metric is robust to given 
    weight assumptions.
    Optionally uploads the results to the database.

    Parameters
    ----------
    city_name: str
        City name
    target_group: str
        Group to be swept (ie, infrastructure, physical, traffic, regulation) - use "all" to sweep all
    delta_range: float
        Sweep range, e.g., 0.2
    weights_config_path : Path
        Path to the weights configuration file used.
    metrics_config_path : Path
        Path to the metrics configuration file.
    upload : bool, optional
        If True, upload processed network segments and metrics to PostGIS.
    """

    # Weight step used for sweep (hardcoded for now)
    eps = 0.05

    # Get config info
    #(remove version info from resulting dict)
    weights_config = read_config("weights", "yaml", weights_config_path)
    weights_config.pop("version")

    metrics_config = read_config("cyclability", "yaml", metrics_config_path)
    metrics_config.pop("version")

    # Clear-up database
    logging.info("DELETE WEIGHT SWEEP DATABASE (IF PRESENT)")
    delete_city_rows("group_sensitivity", city_name, target_group)


    # Init bike_infra values for which score is 1.0 (track, etc.)
    # Dict used in prepare_cyclability_segment for maxspeed missing info definition
    # Defined here to avoid definition at each gdf row and at each chunk 
    bike_infra_mapping = metrics_config["bike_infrastructure"]["mapping"]
    excellent_bike_infra = {k for k, v in bike_infra_mapping.items() if v == 1.0}

    # Retrieve segments from PostGIS
    logging.info("LOAD SEGMENTS")
    gdf = load_segments_for_metrics_recompute(city_name)

    # Perform sweep sensitivty analysis for given group
    sweep_city_score_result, delta_group_weight = sweep_group_weight(gdf, 
                                                                     target_group, 
                                                                     eps, 
                                                                     delta_range,
                                                                     weights_config,
                                                                     metrics_config,
                                                                     metrics_config_path,
                                                                     excellent_bike_infra)

    # Compute local sensitivity slope at baseline weight w₀
    baseline_index = delta_group_weight.index(0.0)

    sensitivity = (sweep_city_score_result[baseline_index + 1] - sweep_city_score_result[baseline_index - 1]) / eps

    if upload == True:

        logging.info(f"SAVE {city_name} CITY METRICS FROM {target_group} SWEEP TO DATABASE")
        # Prepare data to be uploaded to PostGIS database (city_metrics table)
        df_prepared = prepare_group_sweep_city_metrics_df_for_postgis(city_name, 
                                                                'cyclability',
                                                                metrics_config_path,
                                                                target_group,
                                                                delta_group_weight,
                                                                sweep_city_score_result,
                                                                sensitivity)
        
        # Upload dataframe to PostGIS
        dataframe_to_postgres(df_prepared, 
                              'group_sensitivity', 
                              'df', 
                              'append')