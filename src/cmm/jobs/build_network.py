import click
import logging 

@click.command()
@click.option("--c", "--city-name", "city_name", type = str, required = True)
@click.option("--south", type = float, required = True)
@click.option("--west", type = float, required = True)
@click.option("--north", type = float, required = True)
@click.option("--east", type = float, required = True)
def main(city_name, south, west, north, east):
    from cmm.services.pipeline import build_network_from_api
    from cmm.utils.misc import get_project_root
    from cmm.data.ingest.overpass_queries import roads_in_bbox
    from cmm.data.export.postgres import delete_city_rows
    from cmm.data.export.postgres import reference_area_to_postgres
    from cmm.utils.geometry import geom_from_bbox

    root = get_project_root()

    # Define API query
    query = roads_in_bbox(
        south, west,
        north, east
    )

    # Clear-up database
    logging.info("CLEAR DATABASE")
    delete_city_rows("network_segments", city_name)
    delete_city_rows("refresh_areas", city_name)
    # segment_metrics is deleted automatically (postgres)
    
    # Define reference geometry from bbox (polygon)
    ref_geometry = geom_from_bbox(south, west, north, east)

    # Create/update reference area in PostGIS database
    logging.info("SAVE REFERENCE AREA")
    reference_area_to_postgres(city_name, ref_geometry)

    # Run pipeline
    build_network_from_api(
        city_name = city_name,
        query = query,
        weights_config_path = root / "src/cmm/metrics/config/weights.yaml",
        cyclability_config_path = root / "src/cmm/metrics/config/cyclability.yaml"
    )

    logging.info("DONE")
if __name__ == "__main__":
    main()