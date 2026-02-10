import click
import logging
from pathlib import Path

@click.command()
@click.option("--city", "city_name", type = str, required = True)
@click.option("--out", "output_dir", type = click.Path(path_type = Path), default = None)
@click.option("--overwrite", is_flag = True)
def main(city_name: str, output_dir: Path | None, overwrite: bool):
    """
    Generate a static Kepler.gl HTML map for a given city.
    """
    from city_metrics.services.maps import create_static_map
    from city_metrics.utils.misc import get_project_root

    logging.basicConfig(level = logging.INFO)

    root = get_project_root()

    # Resolve output directory
    if output_dir is None:
        output_dir = root / "static_maps"

    # Create output folder
    # Create parents if necessary, if exists keep going
    output_dir.mkdir(parents = True, exist_ok = True)

    # Resolve Kepler config
    kepler_config_path = (root / "frontend" / "kepler" / "kepler_config.json")

    output_file = output_dir / f"{city_name}.html"

    create_static_map(city_name, kepler_config_path, output_dir, overwrite)

    logging.info("Static map written to: %s", output_file)
    logging.info("DONE")

if __name__ == "__main__":
    main()