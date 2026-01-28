
from pathlib import Path
import logging
from city_metrics.data.ingest.geojson_loader import geojson_to_gdf
from city_metrics.data.ingest.overpass_client import run_overpass_query
from city_metrics.data.ingest.overpass_parser import overpass_elements_to_geojson 
from city_metrics.validation.geometry import validate_gdf_linestrings
from city_metrics.data.normalize.cleaning import restrict_gdf
from city_metrics.data.normalize.cleaning import normalize_maxspeed_info
from city_metrics.metrics.compute_metrics import define_augmented_geodataframe
from city_metrics.data.export.postgres import prepare_network_segments_gdf_for_postgis
from city_metrics.data.export.postgres import prepare_metrics_df_for_postgis
from city_metrics.data.export.postgres import dataframe_to_postgres
from city_metrics.utils.geometry import geodesic_length
from city_metrics.utils.config_helpers import read_config
from city_metrics.data.export.postgres import delete_city_rows

def build_network_from_api(city_name: str,
                            query: str,
                            weights_config_path: Path,
                            metrics_config_path: Path,
                            upload: bool = True,
                            chunk_size: int = 5000) -> None:
    """
    Build road network from an Overpass API query and compute cyclability metrics.
    Optionally uploads processed network segments and metrics to PostGIS.

    For better memory handling, the pipeline is called by splitting the inbound data in chunks 
    (maximum size per chunk is determined by chunk_size)

    Parameters
    ----------
    city_name: str
        Name of given city (e.g., "oslo").
    query : str
        Overpass QL query used to fetch data.
    weights_config_path : Path
        Path to the weights configuration file used.
    metrics_config : Path
        Path to the metrics (cyclability) configuration file.
    upload : bool, optional
        If True, upload processed network segments and metrics to PostGIS.
    chunk_size: int
        Number of features per gdf chunk
    """
    
    # Get config info
    #(remove version info from resulting dict)
    weights_config = read_config("weights", "yaml", weights_config_path)
    weights_config.pop("version")

    metrics_config = read_config("cyclability", "yaml", metrics_config_path)
    metrics_config.pop("version")

    # Init bike_infra values for which score is 1.0 (track, etc.)
    # Dict used in prepare_cyclability_segment for maxspeed missing info definition
    # Defined here to avoid definition at each gdf row and at each chunk 
    bike_infra_mapping = metrics_config["bike_infrastructure"]["mapping"]
    excellent_bike_infra = {k for k, v in bike_infra_mapping.items() if v == 1.0}

    # Clear-up existing database info
    logging.info("CLEAR DATABASE")
    delete_city_rows("network_segments", city_name)
    # segment_metrics is deleted automatically (postgres)

    logging.info("API FETCH")
    # Fetch data from API
    data_json = run_overpass_query(query, 200, 50, 2.0)
    data_geojson = overpass_elements_to_geojson(data_json["elements"])
    
    logging.info(f"CREATE GDF CHUNKS")
    logging.info(f"Maximum chunk size: {chunk_size}")

    gdf_chunks = geojson_to_gdf(data_geojson, chunk_size)
    total_chunks = len(gdf_chunks)  

    logging.info(f"PROCESS GDF CHUNKS")
    for idx, gdf_chunk in enumerate(gdf_chunks, start = 1):

        logging.info(f"Process gdf chunk: {idx}/{total_chunks}")
        # Transformation layer
        logging.info(f"Transform data for gdf chunk: {idx}")
        gdf_chunk = validate_gdf_linestrings(gdf_chunk) # Validate geometry
        gdf_chunk = restrict_gdf(gdf_chunk) # Restrict data
        gdf_chunk = normalize_maxspeed_info(gdf_chunk) # Normalize maxspeed info to km/h

        # Ensure every segment has ID
        #if 'id' not in gdf_chunk.columns or gdf_chunk['id'].isna().any():
        #    logging.warning(f"Chunk {idx} has missing segment IDs. Generating temporary IDs.")
        #    gdf_chunk = gdf_chunk.reset_index(drop=True)
        #    gdf_chunk['id'] = gdf_chunk.index.astype(str)  # simple string ID

        # ---- length-only computation (meters) ----
        gdf_chunk["segment_length"] = gdf_chunk.geometry.apply(geodesic_length) 

        # Compute metrics and augment dataframe
        logging.info(f"Compute metrics for gdf chunk: {idx}")
        gdf_chunk, metrics_features_scores = define_augmented_geodataframe(gdf_chunk, 
                                                                        weights_config, 
                                                                        metrics_config,
                                                                        metrics_config_path,
                                                                        excellent_bike_infra)
            
        if upload == True:
            logging.info(f"Save gdf chunk {idx} to database")
            # Prepare segments GDF for PostGIS upload
            gdf_proc_prepared = prepare_network_segments_gdf_for_postgis(city_name, gdf_chunk)

            # Upload network segments data to PostGIS
            dataframe_to_postgres(gdf_proc_prepared, 'network_segments', 'gdf', 'append')

            # Prepare metrics GDF for PostGIS upload 
            df_metrics_prepared = prepare_metrics_df_for_postgis(city_name, gdf_chunk, metrics_features_scores, 'cyclability', metrics_config_path)

            # Upload metrics GDF to PostGIS
            dataframe_to_postgres(df_metrics_prepared, 'segment_metrics', 'df', 'append')
            