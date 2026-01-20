from pathlib import Path
import logging

from cmm.utils.geometry import bbox_from_geom
from cmm.data.ingest.overpass_queries import roads_in_bbox
from cmm.services.pipeline import build_network_from_api
from cmm.data.export.postgres import delete_segment_metrics_in_bbox
from cmm.data.export.postgres import delete_segments_in_bbox
from cmm.data.export.postgres import load_reference_area

def refresh_osm_data(refresh_geom_name: str,
                        weights_config_path: Path,
                        cyclability_config_path: Path,
                        upload: bool = True) -> None:
    """
    Refresh network and recompute metrics associated with bounding box covering segments present in
    the database. 

    Parameters
    ----------
    refresh_geom_name: str
        Reference geometry to be used for refresh bounding box.
    weights_config_path : Path
        Path to the weights configuration file used.
    cyclability_config_path : Path
        Path to the cyclability configuration file.
    upload : bool, optional
        If True, upload processed network segments and metrics to PostGIS.
    """

    # Retrieve reference geometry from PostGIS database
    logging.info("LOAD REFERENCE AREA")
    refresh_geom = load_reference_area(refresh_geom_name)
    
    # Derive bounding box from existing reference refresh geometry
    south, west, north, east = bbox_from_geom(refresh_geom)

    # Define refresh query
    query = roads_in_bbox(
        south, west,
        north, east
    )

    # Clear-up database - segments within refresh bounding box
    logging.info("CLEAR DATABASE")
    delete_segment_metrics_in_bbox(south, west, north, east)
    delete_segments_in_bbox(south, west, north, east)

    # Run refresh pipeline

    build_network_from_api(
        query = query,
        weights_config_path = weights_config_path,
        cyclability_config_path = cyclability_config_path,
        upload = upload
    )

    logging.info("DONE.")