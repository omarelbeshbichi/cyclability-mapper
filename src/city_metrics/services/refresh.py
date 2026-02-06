from pathlib import Path
import logging
from city_metrics.data.ingest.overpass_queries import roads_in_bbox, roads_in_polygon
from city_metrics.services.pipeline import build_network_from_api
from city_metrics.data.export.postgres import delete_segment_metrics_in_polygon
from city_metrics.data.export.postgres import delete_segments_in_polygon
from city_metrics.data.export.postgres import load_reference_area
from typing import Optional
from city_metrics.data.ingest.geocoding import city_to_polygon, split_polygon_into_bboxes

def refresh_osm_data(city_name: str,
                        weights_config_path: Path,
                        metrics_config_path: Path,
                        upload: bool = True,
                        chunk_size: int = 5000,
                        timeout: Optional[int] = 50,
                        tiling: Optional[bool] = False,
                        retries: Optional[int] = 50,
                        delay: Optional[float] = 2.0) -> None:
    """
    Refresh network and recompute metrics associated with reference polygon covering segments present 
    in the database. 

    Parameters
    ----------
    city_name: str
        Name of given city (e.g., "oslo").
    weights_config_path : Path
        Path to the weights configuration file used.
    metrics_config_path : Path
        Path to the cyclability configuration file.
    upload : bool, optional
        If True, upload processed network segments and metrics to PostGIS.
    timeout: Optional[int]
        Overpass API timeout.
    """

    # Retrieve reference polygon from PostGIS database
    logging.info("LOAD REFERENCE POLYGON")
    ref_polygon = load_reference_area(city_name)
    
    if tiling:
        tiles = split_polygon_into_bboxes(ref_polygon, step_deg=0.04)
    else:
        # Define refresh query
        query = roads_in_polygon(ref_polygon, timeout)

    # Clear-up database - segments within refresh polygon
    logging.info(f"CLEAR DATABASE FOR {city_name} METRICS")
    delete_segment_metrics_in_polygon(city_name, ref_polygon)
    delete_segments_in_polygon(city_name, ref_polygon)

    if tiling:
        for i, (south, west, north, east) in enumerate(tiles, 1):
            logging.info("PROCESSING TILE %d / %d", i, len(tiles))

            query = roads_in_bbox(south, west, north, east, timeout)

            # Run refresh pipeline
            build_network_from_api(
                city_name = city_name,
                query = query,
                weights_config_path = weights_config_path,
                metrics_config_path = metrics_config_path,
                upload = upload,
                chunk_size = chunk_size,
                timeout=timeout,
                retries=retries,
                delay=delay
            )
    else:
        # Run refresh pipeline
            build_network_from_api(
                city_name = city_name,
                query = query,
                weights_config_path = weights_config_path,
                metrics_config_path = metrics_config_path,
                upload = upload,
                chunk_size = chunk_size,
                timeout=timeout,
                retries=retries,
                delay=delay
            )