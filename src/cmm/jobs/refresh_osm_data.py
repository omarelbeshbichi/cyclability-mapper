import click
import logging

@click.command()
@click.option("--c", "--city-name", "city_name", type = str, required = True)
@click.option("--chunk", "chunk_size", type = int, default = 5000, required = False)
def main(city_name, chunk_size):

    from cmm.services.refresh import refresh_osm_data
    from cmm.utils.misc import get_project_root

    root = get_project_root()

    refresh_osm_data(
        city_name = city_name,
        weights_config_path = root  / "src/cmm/metrics/config/weights.yaml",
        cyclability_config_path =  root  / "src/cmm/metrics/config/cyclability.yaml",
        upload = True,
        chunk_size = chunk_size
    )
    
    logging.info("DONE.")
if __name__ == "__main__":
    main()