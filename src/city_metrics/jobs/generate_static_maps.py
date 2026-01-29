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

    from frontend.kepler.map import create_map
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

    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"Static map already exists: {output_file}. "
            "Use --overwrite to regenerate."
        )

    logging.info("Generating static Kepler map for city: %s", city_name)

    # Create Kepler map
    m = create_map(city_name, kepler_config_path)

    # Write HTML directly (no temp files)
    m.save_to_html( file_name = str(output_file), read_only = True)

    # ---- FULLSCREEN FIX (same as FastAPI) ----
    style_fix = """
    <style>
        html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        #kepler-gl__map {
            width: 100vw !important;
            height: 100vh !important;
        }
    </style>
    """

    html_content = output_file.read_text(encoding="utf-8")
    output_file.write_text(style_fix + html_content, encoding="utf-8")
    # ------------------------------------------

    logging.info("Static map written to: %s", output_file)
    logging.info("DONE")


if __name__ == "__main__":
    main()