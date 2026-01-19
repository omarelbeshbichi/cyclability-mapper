
from pathlib import Path

from cmm.data.ingest.geojson_loader import geojson_to_gdf
from cmm.data.ingest.overpass_client import run_overpass_query
from cmm.data.ingest.overpass_parser import overpass_elements_to_geojson 
from cmm.validation.geometry import validate_gdf_linestrings
from cmm.data.normalize.cleaning import restrict_gdf
from cmm.data.normalize.cleaning import normalize_maxspeed_info
from cmm.metrics.compute_metrics import define_augmented_geodataframe
from cmm.data.export.postgres import prepare_network_segments_gdf_for_postgis
from cmm.data.export.postgres import prepare_metrics_df_for_postgis
from cmm.data.export.postgres import dataframe_to_postgres

def build_network_from_api(query: str,
                           weights_config_path: Path,
                           cyclability_config_path: Path,
                           upload: bool = True) -> None:
    """
    Text
    """

    # Fetch data from API
    data_json = run_overpass_query(query, 200, 50, 2.0)
    data_geojson = overpass_elements_to_geojson(data_json["elements"])
    gdf = geojson_to_gdf(data_geojson)

    # Transformation layer
    gdf_proc = validate_gdf_linestrings(gdf) # Validate geometry
    gdf_proc = restrict_gdf(gdf_proc) # Restrict data to only needed
    gdf_proc = normalize_maxspeed_info(gdf_proc) # Normalize maxspeed info to km/h

    # Compute metrics and augment dataframe
    gdf_proc, metrics_features_scores = define_augmented_geodataframe(gdf_proc, 
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
