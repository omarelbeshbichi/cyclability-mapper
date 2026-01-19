
from pathlib import Path

from cmm.services.metrics.loader import load_segments_for_metrics_recompute
from cmm.metrics.compute_metrics import define_augmented_geodataframe
from cmm.data.export.postgres import prepare_network_segments_gdf_for_postgis
from cmm.data.export.postgres import prepare_metrics_df_for_postgis
from cmm.data.export.postgres import dataframe_to_postgres

def recompute_metrics_from_postgis(weights_config_path: Path,
                                    cyclability_config_path: Path,
                                    upload: bool = True) -> None:
    """
    Recompute cyclability metrics for existing network segments stored in PostGIS.
    Optionally uploads the updated segments and metrics back to the database.

    Parameters
    ----------
    weights_config_path : Path
        Path to the weights configuration file used.
    cyclability_config_path : Path
        Path to the cyclability configuration file.
    upload : bool, optional
        If True, upload processed network segments and metrics to PostGIS.
    """

    # Retrieve segments from PostGIS
    gdf = load_segments_for_metrics_recompute()

    # Compute metrics and augment dataframe
    gdf_proc, metrics_features_scores = define_augmented_geodataframe(gdf, 
                                                                    weights_config_path, 
                                                                    cyclability_config_path)
        
    if upload == True:
        # Prepare segments GDF for PostGIS upload
        gdf_proc_prepared = prepare_network_segments_gdf_for_postgis(gdf_proc)

        # Upload network segments data to PostGIS
        dataframe_to_postgres(gdf_proc_prepared, 'network_segments', 'gdf', 'append')

        # Prepare metrics GDF for PostGIS upload 
        df_metrics_prepared = prepare_metrics_df_for_postgis(gdf_proc, metrics_features_scores, 'cyclability', cyclability_config_path)

        # Upload metrics GDF to PostGIS
        dataframe_to_postgres(df_metrics_prepared, 'segment_metrics', 'df', 'append')
