import click
import logging

@click.command()
@click.option("--city", "--city-name", "city_name", type = str, required = True)
@click.option("--chunk", "chunk_size", type = int, default = 5000, required = False)
@click.option("--tout", "timeout", type = int, default = 50, required = False)
@click.option("--tiling/--no-tiling", default=False, required= False)
@click.option("--retries", default = 50, required= False)
@click.option("--delay", default = 2.0, required= False)
def main(city_name, chunk_size, timeout, tiling, retries, delay):
    from city_metrics.services.refresh import refresh_osm_data
    from city_metrics.utils.misc import get_project_root
    from city_metrics.services.metrics.compute import compute_city_metrics_from_postgis
    from city_metrics.utils.config_helpers import read_config

    root = get_project_root()

    weights_config_path = root / "src/city_metrics/metrics/config/weights.yaml"
    metrics_config_path = root / "src/city_metrics/metrics/config/cyclability.yaml"

    refresh_osm_data(
        city_name = city_name,
        weights_config_path = weights_config_path,
        metrics_config_path = metrics_config_path,
        upload = True,
        chunk_size = chunk_size,
        timeout = timeout,
        tiling = tiling,
        retries = retries,
        delay = delay
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