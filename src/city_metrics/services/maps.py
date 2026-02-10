import logging
from frontend.kepler.map import create_map
from pathlib import Path

def create_static_map(city_name: str, 
                      kepler_config_path: Path,
                      output_dir: Path,
                      overwrite: bool = True) -> None:
    """
    Generate static HTML Kepler.gl-based map and saves it in output directory.

    Parameters
    ----------
    city_name: str
        City name
    kepler_config_path: Path
        Path to the Kepler.gl JSON config file
    output_dir: Path
        Path to the output directory where static HTML map will be saved
    overwrite: bool
        Bool flag to determine whether already existing data should be overwritten
    """

    # Static map name
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