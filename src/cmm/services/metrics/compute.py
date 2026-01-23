
from pathlib import Path
import logging 

from cmm.services.metrics.loader import load_segments_for_metrics_recompute, load_data_for_city_metrics_compute
from cmm.metrics.compute_metrics import define_augmented_geodataframe, compute_total_city_metrics
from cmm.data.export.postgres import prepare_metrics_df_for_postgis, prepare_total_city_metrics_df_for_postgis
from cmm.data.export.postgres import delete_city_rows
from cmm.data.export.postgres import dataframe_to_postgres
from cmm.utils.config_reader import read_config

def recompute_metrics_from_postgis(city_name: str,
                                    weights_config_path: Path,
                                    metrics_config_path: Path,
                                    upload: bool = True) -> None:
    """
    Recompute cyclability metrics for existing network segments stored in PostGIS.
    Optionally uploads the updated segments and metrics back to the database.

    Parameters
    ----------
    city_name: str
        Name of given city (e.g., "oslo").
    weights_config_path : Path
        Path to the weights configuration file used.
    cyclability_config_path : Path
        Path to the cyclability configuration file.
    upload : bool, optional
        If True, upload processed network segments and metrics to PostGIS.
    """

    # Get config info
    #(remove version info from resulting dict)
    weights_config = read_config("weights", "yaml", weights_config_path)
    weights_config.pop("version")

    metrics_config = read_config("cyclability", "yaml", metrics_config_path)
    metrics_config.pop("version")

    # Retrieve segments from PostGIS
    logging.info("LOAD SEGMENTS")
    gdf = load_segments_for_metrics_recompute(city_name)

    # Compute metrics and augment dataframe
    logging.info("COMPUTE METRICS")
    gdf_proc, metrics_features_scores = define_augmented_geodataframe(gdf, 
                                                                    weights_config, 
                                                                    metrics_config)
        
    if upload == True:

        # Clear-up metrics database
        logging.info(f"CLEAR DATABASE FOR {city_name} METRICS")
        delete_city_rows("segment_metrics", city_name)

        logging.info(f"SAVE {city_name} METRICS TO DATABASE")
        # Prepare metrics GDF for PostGIS upload (takes care of ID match with network_segments)
        df_metrics_prepared = prepare_metrics_df_for_postgis(city_name, 
                                                             gdf_proc, 
                                                             metrics_features_scores, 
                                                             'cyclability', 
                                                             metrics_config_path)

        # Upload metrics GDF to PostGIS
        dataframe_to_postgres(df_metrics_prepared, 
                              'segment_metrics', 
                              'df', 
                              'append')



def compute_city_metrics_from_postgis(city_name: str,
                                        metrics_config_path: Path,
                                        upload: bool = True) -> None:
    """
    Compute overall cyclability metrics (and percentage missing data) for given city stored in PostGIS.
    Optionally uploads the metrics and missing data info to the database (city_metrics table).

    Parameters
    ----------
    city_name: str
        Name of given city (e.g., "oslo").
    cyclability_config_path : Path
        Path to the cyclability configuration file.
    upload : bool, optional
        If True, upload processed network segments and metrics to PostGIS.
    """

    # Clear-up database
    logging.info("DELETE CITY METRICS (IF PRESENT)")
    delete_city_rows("city_metrics", city_name)

    # Load info from PostGIS
    logging.info("LOAD CITY DATA")
    gdf = load_data_for_city_metrics_compute(city_name)

    # Compute overall city metrics and assocaited features uncertainty
    logging.info("COMPUTE CITY METRICS")
    total_city_score, city_missing_features = compute_total_city_metrics(gdf)

    if upload == True:

        logging.info(f"SAVE {city_name} CITY METRICS TO DATABASE")
        # Prepare data to be uploaded to PostGIS database (city_metrics table)
        df_prepared = prepare_total_city_metrics_df_for_postgis(city_name, 
                                                                'cyclability',
                                                                metrics_config_path,
                                                                total_city_score,
                                                                city_missing_features)
        
        # Upload metrics GDF to PostGIS
        dataframe_to_postgres(df_prepared, 
                              'city_metrics', 
                              'df', 
                              'append')