from pathlib import Path
import logging 
from city_metrics.services.metrics.loader import load_segments_for_metrics_recompute
from city_metrics.metrics.compute_metrics import define_augmented_geodataframe, compute_total_city_metrics
from city_metrics.utils.config_helpers import read_config
import numpy as np
from city_metrics.data.export.postgres import dataframe_to_postgres
from city_metrics.data.export.postgres import prepare_group_sweep_city_metrics_df_for_postgis
from city_metrics.utils.geometry import geodesic_length
from city_metrics.data.export.postgres import delete_city_rows

def sensitivity_single_weight_sweep(city_name: str,
                                    target_group: str, 
                                    delta_range: float,
                                    weights_config_path: Path,
                                    metrics_config_path: Path,
                                    upload: bool = True) -> None:
    """
    Perform sweep sensitivity analysis on group weights employed for given city.
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

    # Get original group weights
    original_weights = {k: v["weight"] for k, v in weights_config["cyclability"].items()}

    # Get original group weight
    base_group_weight = weights_config["cyclability"][target_group]["weight"]

    # Number of steps to sweep
    num_steps = int((delta_range * 2) / eps) + 1
    deltas = np.linspace(-delta_range, delta_range, num_steps)

    sweep_city_score_result = []
    delta_group_weight = []

    for d in deltas:
        
        # Create new weights dictionary for this iteration
        current_weights = original_weights.copy()

        if d != 0.0:
            # Apply delta and keep within [0, 1]
            new_val = np.clip(base_group_weight + d, 0, 1)
            current_weights[target_group] = new_val

            # Normalize: ensure the sum of all groups is exactly 1.0
            total = sum(current_weights.values())
            if total > 0:
                for k in current_weights:
                    current_weights[k] /= total

        # Update the weights_config object with normalized values
        for k, v in current_weights.items():
            weights_config["cyclability"][k]["weight"] = v

        logging.info(f"Step Delta {d:+.2f} | {target_group} weight: {weights_config['cyclability'][target_group]['weight']:.4f}")

        # Compute metrics and augment dataframe
        gdf_proc, _ = define_augmented_geodataframe(gdf, 
                                                    weights_config, 
                                                    metrics_config,
                                                    metrics_config_path,
                                                    excellent_bike_infra)

        # ---- adapt GeoDataFrame to general pipeline ----
        gdf_proc["segment_length"] = gdf_proc.geometry.apply(geodesic_length) 
        gdf_proc = gdf_proc.rename(columns={"cyclability_metrics": "total_score"})

        # Compute total city metrics    
        logging.info(f"COMPUTE CITY METRICS FOR WEIGHT DELTA: {d}")
        total_city_score, _, _ = compute_total_city_metrics(gdf_proc, 
                                                            "cyclability", 
                                                            weights_config)
        sweep_city_score_result.append(total_city_score)
        delta_group_weight.append(d)


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