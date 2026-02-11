import click
import logging
from pathlib import Path

@click.command()
@click.option("--city", "--city-name", "city_name", type = str, required = True)
@click.option("--chunk", "chunk_size", type = int, default = 5000, required = False)
@click.option("--tout", "timeout", type = int, default = 50, required = False)
@click.option("--tiling/--no-tiling", default=False, required= False)
@click.option("--retries", default = 50, required= False)
@click.option("--delay", default = 2.0, required= False)
@click.option("--out", "output_dir", type = click.Path(path_type = Path), default = None, required = False)

def main(city_name, chunk_size, timeout, tiling, retries, delay, output_dir):
    from city_metrics.services.refresh import refresh_osm_data
    from city_metrics.utils.misc import get_project_root
    from city_metrics.services.metrics.compute import compute_city_metrics_from_postgis
    from city_metrics.utils.config_helpers import read_config
    from city_metrics.services.maps import create_static_map, create_static_metrics_scatter

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

    logging.info("GENERATE STATIC MAP")
    # Resolve output directory
    if output_dir is None:
        output_dir = root / "static_maps"
    # Create output folder if it does not exist
    output_dir.mkdir(parents = True, exist_ok = True)
    
    kepler_config_path = (root / "frontend" / "kepler" / "kepler_config.json")
    
    create_static_map(city_name, kepler_config_path, output_dir, True)
    create_static_metrics_scatter(output_dir, True)

    logging.info("DONE")
if __name__ == "__main__":
    main()