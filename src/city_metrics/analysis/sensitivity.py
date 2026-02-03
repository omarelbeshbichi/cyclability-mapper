import numpy as np
from geopandas import gpd
from pathlib import Path
from typing import Tuple
import logging
from city_metrics.metrics.compute_metrics import define_augmented_geodataframe, compute_total_city_metrics
from city_metrics.utils.geometry import geodesic_length


def sweep_group_weight(gdf: gpd.GeoDataFrame,
                    target_group: str, 
                    eps: float,
                    delta_range: float,
                    weights_config: dict,
                    metrics_config: dict,
                    metrics_config_path: Path,
                    excellent_bike_infra: dict) -> Tuple[list, list]:
    """
    Perform sensitivity sweep of group weight.

    Parameters
    ----------
    gdf: gpd.GeoDataFrame
        GeoDataFrame of city information
    target_group: str
        Name of group to be swept (e.g., "infrastructure", "physical", etc.)
    eps: float
        Weight variation (e.g., 0.05)
    delta_range: float
        Max variation range of weight (e.g., 0.2)
    weights_config: dict
        Dictionary storing weight YAML
    metrics_config: dict
        Dictionary storing metrics configuration info from YAML
    metrics_config_path: Path
        Path of metrics config YAML
        excellent_bike_infra: dict
        Dict from YAML file defining bike_infrastructure metrics features from YAML file for which score is 1.0

    Returns
    -------
    sweep_city_score_result: list
        City metrics score for each group weight variation
    delta_group_weight: list
        Group weight variations used in the sweep
    """

    # Store group names
    group_names = list(weights_config["cyclability"].keys())

    # Extract base weights from YAML dict
    base_weights = np.array(
        [weights_config["cyclability"][k]["weight"] for k in group_names]
    )

    # Get index of target group
    target_idx = group_names.index(target_group)

    # Number of steps to sweep
    num_steps = int((delta_range * 2) / eps) + 1
    deltas = np.linspace(-delta_range, delta_range, num_steps)

    ## Perform weight sweep
    # Tile base weights num_steps times
    W = np.tile(base_weights, (num_steps, 1)) # Repeat base_weights num_steps rows x 1 col

    # Add deltas to weights using broadcast (keep within [0, 1])
    W[:, target_idx] = np.clip(
        base_weights[target_idx] + deltas,
        0.0,
        1.0
    )

    # Normalize rows (sum should be always = 1)
    row_sums = W.sum(axis = 1, keepdims = True)
    W = np.divide(W, row_sums, where = row_sums > 0)

    # Perform actual sweep
    sweep_city_score_result = []
    for i, weights_row in enumerate(W):

        for k, val in zip(group_names, weights_row):
            weights_config["cyclability"][k]["weight"] = float(val)

        logging.info(
            f"Step Delta {deltas[i]:+.2f} | "
            f"{target_group} weight: {weights_row[target_idx]:.4f}"
        )

        # compute metrics
        gdf_proc, _ = define_augmented_geodataframe(
            gdf,
            weights_config,
            metrics_config,
            metrics_config_path,
            excellent_bike_infra,
        )

        # ---- adapt GeoDataFrame to general pipeline ----
        gdf_proc["segment_length"] = gdf_proc.geometry.apply(geodesic_length) 
        gdf_proc = gdf_proc.rename(columns={"cyclability_metrics": "total_score"})


        # Compute total city metrics    
        logging.info(f"COMPUTE CITY METRICS FOR WEIGHT DELTA: {deltas[i]:+.2f}")
        total_city_score, _, _ = compute_total_city_metrics(gdf_proc, 
                                                            "cyclability", 
                                                            weights_config)

        sweep_city_score_result.append(total_city_score)


    return sweep_city_score_result, deltas.tolist()