from pathlib import Path
import logging

from cmm.data.ingest.overpass_queries import roads_in_polygon
from cmm.services.pipeline import build_network_from_api
from cmm.data.export.postgres import delete_segment_metrics_in_polygon
from cmm.data.export.postgres import delete_segments_in_polygon
from cmm.data.export.postgres import load_reference_area

def refresh_osm_data(city_name: str,
                        weights_config_path: Path,
                        cyclability_config_path: Path,
                        upload: bool = True,
                        chunk_size: int = 5000) -> None:
    """
    Refresh network and recompute metrics associated with reference polygon covering segments present 
    in the database. 

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

    # Retrieve reference polygon from PostGIS database
    logging.info("LOAD REFERENCE POLYGON")
    ref_polygon = load_reference_area(city_name)
    
    # Define refresh query
    query = roads_in_polygon(ref_polygon)

    # Clear-up database - segments within refresh polygon
    logging.info(f"CLEAR DATABASE FOR {city_name} METRICS")
    delete_segment_metrics_in_polygon(city_name, ref_polygon)
    delete_segments_in_polygon(city_name, ref_polygon)

    # Run refresh pipeline
    build_network_from_api(
        city_name = city_name,
        query = query,
        weights_config_path = weights_config_path,
        cyclability_config_path = cyclability_config_path,
        upload = upload,
        chunk_size = chunk_size
    )