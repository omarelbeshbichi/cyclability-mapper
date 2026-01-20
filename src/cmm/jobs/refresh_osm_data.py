import click
import logging

@click.command()
def main():

    from cmm.services.refresh import refresh_osm_data
    from cmm.utils.misc import get_project_root

    root = get_project_root()

    refresh_osm_data(
        refresh_geom_name = "city1", # Placeholder city name for now
        weights_config_path = root  / "src/cmm/metrics/config/weights.yaml",
        cyclability_config_path =  root  / "src/cmm/metrics/config/cyclability.yaml",
    )
    
    logging.info("DONE.")
if __name__ == "__main__":
    main()