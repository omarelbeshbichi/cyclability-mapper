
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
from sqlalchemy import create_engine
import os
import pandas as pd

def build_network_from_api(city_name: str,
                            query: str,
                            weights_config_path: Path,
                            metrics_config_path: Path,
                            upload: bool = True,
                            chunk_size: int = 5000,
                            timeout: int = 200,
                            retries: int = 50,
                            delay: float = 2.0) -> None:
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
    timeout: int
        Timeout for Overpass API in seconds
    retries: int
        Number of connection retries for Overpass API
    delay: float
        Delay in seconds between Overpass API connections
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

    logging.info("API FETCH")
    # Fetch data from API
    data_json = run_overpass_query(query, timeout, retries, delay)
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

        # Skip chunk if empty or has no geometry
        if gdf_chunk.empty or gdf_chunk.geometry.isnull().all():
            logging.warning(f"Chunk {idx} has no valid geometries after normalization. Skipping.")
            continue

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


            # Connect to PostGIS to retrieve currently stored segments
            # (if using tiles - they can have segments in common, so duplicates in next line should be dropped)

            DATABASE_URL = os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://user:pass@localhost:5432/db"
            )
            engine = create_engine(DATABASE_URL)

            # Fetch existing segments IDs (osm_id) for this city
            existing_osm_ids = set(pd.read_sql(
                "SELECT osm_id FROM network_segments WHERE city_name = %(city_name)s",
                engine,
                params={"city_name": city_name}
            )["osm_id"])
            
            # Also fetch metrics associated with existing segments IDs for this city
            existing_metrics = pd.read_sql(
                """
                SELECT segment_id
                FROM segment_metrics
                WHERE metric_name = %(metric_name)s
                AND segment_id IN (
                    SELECT id
                    FROM network_segments
                    WHERE city_name = %(city_name)s
                )
                """,
                engine,
                params={
                    "city_name": city_name,
                    "metric_name": "cyclability"
                }
            )
            existing_metric_ids = set(existing_metrics["segment_id"])

            # Drop segments already present in database
            mask_drop = ~gdf_proc_prepared["osm_id"].isin(existing_osm_ids)
            gdf_proc_prepared = gdf_proc_prepared[mask_drop]
                       
            # Upload network segments data to PostGIS
            dataframe_to_postgres(gdf_proc_prepared, 'network_segments', 'gdf', 'append')

            # Prepare metrics GDF for PostGIS upload 
            df_metrics_prepared = prepare_metrics_df_for_postgis(city_name, gdf_chunk, metrics_features_scores, 'cyclability', metrics_config_path)


            # Drop metrics associated with segments already present in database
            df_metrics_prepared = df_metrics_prepared[
                ~df_metrics_prepared["segment_id"].isin(existing_metric_ids)
            ]

            # Upload metrics GDF to PostGIS
            dataframe_to_postgres(df_metrics_prepared, 'segment_metrics', 'df', 'append')
            
            # Dispose engine
            engine.dispose()