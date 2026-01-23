import click
import logging

@click.command()
@click.option("--c", "--city-name", "city_name", type = str, required = True)
@click.option("--chunk", "chunk_size", type = int, default = 5000, required = False)
def main(city_name, chunk_size):

    from cmm.services.refresh import refresh_osm_data
    from cmm.utils.misc import get_project_root
    from cmm.services.metrics.compute import compute_city_metrics_from_postgis

    root = get_project_root()

    weights_config_path = root / "src/cmm/metrics/config/weights.yaml"
    metrics_config_path = root / "src/cmm/metrics/config/cyclability.yaml"

    refresh_osm_data(
        city_name = city_name,
        weights_config_path = weights_config_path,
        metrics_config_path = metrics_config_path,
        upload = True,
        chunk_size = chunk_size
    )

    # Compute overall city data and store in PostGIS database
    logging.info("COMPUTE OVERALL CITY METRICS")
    compute_city_metrics_from_postgis(city_name, metrics_config_path, weights_config_path)    

    logging.info("DONE")
if __name__ == "__main__":
    main()