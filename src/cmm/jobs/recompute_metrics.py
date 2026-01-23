import click
import logging

@click.command()
@click.option("--c", "--city-name", "city_name", type = str, required = True)
def main(city_name):

    from cmm.services.metrics.compute import recompute_metrics_from_postgis, compute_city_metrics_from_postgis
    from cmm.utils.misc import get_project_root

    root = get_project_root()

    weights_config_path = root / "src/cmm/metrics/config/weights.yaml"
    metrics_config_path = root / "src/cmm/metrics/config/cyclability.yaml"

    recompute_metrics_from_postgis(
        city_name = city_name,
        weights_config_path = weights_config_path,
        metrics_config_path =  metrics_config_path
    )
    
    # Compute overall city data and store in PostGIS database
    logging.info("COMPUTE OVERALL CITY METRICS")
    compute_city_metrics_from_postgis(city_name, metrics_config_path, weights_config_path)

    logging.info("DONE")
if __name__ == "__main__":
    main()