import click
import logging 

@click.command()
@click.option("--city", "--city-name", "city_name", type = str, required = True)
@click.option("--cc", "--country-code", "country_code", type = str, required = True)
@click.option("--south", type = float, required = False)
@click.option("--west", type = float, required = False)
@click.option("--north", type = float, required = False)
@click.option("--east", type = float, required = False)
@click.option("--chunk", "chunk_size", type = int, default = 5000, required = False)
@click.option("--tout", "timeout", type = int, default = 50, required = False)
@click.option("--tol", "--tolerance", "tolerance", type = float, default = 0.0005, required = False)
def main(city_name, country_code, south, west, north, east, chunk_size, timeout, tolerance):
    from city_metrics.services.pipeline import build_network_from_api
    from city_metrics.utils.misc import get_project_root
    from city_metrics.data.ingest.overpass_queries import roads_in_bbox, roads_in_polygon
    from city_metrics.data.export.postgres import reference_area_to_postgres
    from city_metrics.utils.geometry import geom_from_bbox
    from city_metrics.data.ingest.geocoding import city_to_polygon
    from city_metrics.services.metrics.compute import compute_city_metrics_from_postgis
    from city_metrics.data.export.postgres import delete_city_rows
    from city_metrics.utils.config_helpers import read_config

    root = get_project_root()
    
    weights_config_path = root / "src/city_metrics/metrics/config/weights.yaml"
    metrics_config_path = root / "src/city_metrics/metrics/config/cyclability.yaml"

    if all(v is not None for v in [south, west, north, east]):
        # Build bbox as prescribed as input

        # Define API query
        query = roads_in_bbox(south, west, north, east)

        # Define reference polygon from bbox
        ref_polygon = geom_from_bbox(south, west, north, east)
    else:
        # Build polygon based on city_name
        polygon = city_to_polygon(city_name, 
                                  country_code,
                                  tolerance)
        query = roads_in_polygon(polygon, timeout)
        ref_polygon = polygon
    
    # Create/update reference area in PostGIS database
    logging.info("DELETE OLD REFERENCE POLYGON (IF PRESENT)")
    delete_city_rows("refresh_areas", city_name)
    logging.info("SAVE REFERENCE POLYGON")
    reference_area_to_postgres(city_name, ref_polygon)

    # Run pipeline
    build_network_from_api(
        city_name = city_name,
        query = query,
        weights_config_path = weights_config_path,
        metrics_config_path = metrics_config_path,
        upload = True,
        chunk_size = chunk_size # maximum data chunk size to process in one go
    )

    # Compute overall city data and store in PostGIS database
    logging.info("COMPUTE OVERALL CITY METRICS")
    
    # Get config info
    #(remove version info from resulting dict)
    weights_config = read_config("weights", "yaml", weights_config_path)
    weights_config.pop("version")
    compute_city_metrics_from_postgis(city_name, metrics_config_path, weights_config)
    
    logging.info("DONE")
if __name__ == "__main__":
    main()