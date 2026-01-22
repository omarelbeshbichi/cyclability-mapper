import click
import logging 

@click.command()
@click.option("--c", "--city-name", "city_name", type = str, required = True)
@click.option("--cc", "--country-code", "country_code", type = str, required = True)
@click.option("--south", type = float, required = False)
@click.option("--west", type = float, required = False)
@click.option("--north", type = float, required = False)
@click.option("--east", type = float, required = False)
@click.option("--chunk", "chunk_size", type = int, default = 5000, required = False)
def main(city_name, country_code, south, west, north, east, chunk_size):
    from cmm.services.pipeline import build_network_from_api
    from cmm.utils.misc import get_project_root
    from cmm.data.ingest.overpass_queries import roads_in_bbox, roads_in_polygon
    from cmm.data.export.postgres import delete_city_rows
    from cmm.data.export.postgres import reference_area_to_postgres
    from cmm.utils.geometry import geom_from_bbox
    from cmm.data.ingest.geocoding import city_to_polygon

    timeout = 50

    if all(v is not None for v in [south, west, north, east]):
        # Build bbox as prescribed as input

        # Define API query
        query = roads_in_bbox(south, west, north, east)

        # Define reference polygon from bbox
        ref_polygon = geom_from_bbox(south, west, north, east)
    else:
        # Build polygon based on city_name
        polygon = city_to_polygon(city_name, country_code)
        query = roads_in_polygon(polygon, timeout)
        ref_polygon = polygon

    # Clear-up database
    logging.info("CLEAR DATABASE")
    delete_city_rows("network_segments", city_name)
    delete_city_rows("refresh_areas", city_name)
    # segment_metrics is deleted automatically (postgres)
    
    # Create/update reference area in PostGIS database
    logging.info("SAVE REFERENCE AREA")
    reference_area_to_postgres(city_name, ref_polygon)

    # Run pipeline
    root = get_project_root()

    build_network_from_api(
        city_name = city_name,
        query = query,
        weights_config_path = root / "src/cmm/metrics/config/weights.yaml",
        cyclability_config_path = root / "src/cmm/metrics/config/cyclability.yaml",
        upload = True,
        chunk_size = chunk_size # maximum data chunk size to process in one go
    )

    logging.info("DONE")
if __name__ == "__main__":
    main()