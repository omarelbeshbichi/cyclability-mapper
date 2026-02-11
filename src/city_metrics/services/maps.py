import logging
from frontend.kepler.map import create_map
from pathlib import Path
import re

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

    # Script used to resize Kepler.gl map to viewport
    resize_script = """
    <script>
    window.addEventListener('load', function () {
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
        setTimeout(() => window.dispatchEvent(new Event('resize')), 300);
        setTimeout(() => window.dispatchEvent(new Event('resize')), 600);
    });
    </script>
    """

    # Add header with map title and link to GitHub repository
    header_block = f"""
    <style>

    html, body {{
        margin: 0;
        padding: 0;
        height: 100%;
        overflow: hidden; 
        background: #111;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    .app-header {{
        height: 56px;
        background: #0e0e0e;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 24px;
        box-sizing: border-box;
    }}

    .map-container {{
        height: calc(100vh - 56px);
        width: 100%;
    }}

    .map-container > div {{
        height: 100% !important;
    }}

    .app-title {{
        font-size: 16px;
        font-weight: 500;
        letter-spacing: 0.3px;
    }}

    .app-header a:hover {{
        opacity: 1;
    }}

    .github-link {{
            top: 10px;
            right: 14px;
            z-index: 100000;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
            opacity: 0.85;
            text-decoration: none;
            color: #fff;
            text-decoration: none;
            font-size: 14px;
            opacity: 0.85;
        }}

    .github-link:hover {{
        opacity: 1.0;
    }}

    .github-link img {{
        width: 22px;
        height: 22px;
    }}

    .github-label {{
        font-size: 12px;
        color: #eaeaea;
        background: rgba(0, 0, 0, 0.65);
        padding: 2px 6px;
        border-radius: 4px;
        white-space: nowrap;
    }}
    </style>

    <div class="app-header">
        <div class="app-title">
            Cyclability Mapper - {city_name.capitalize()}
        </div>
        <a class="github-link"
        href="https://github.com/omarelbeshbichi/cyclability-mapper"
        target="_blank">
        <span class="github-label">View source</span>
        <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png">
        </a>
    </div>
    """

    # Retrieve Kepler HTML content
    html = output_file.read_text(encoding="utf-8")
    
    # Define page text
    title = f"Cyclability Mapper - {city_name.capitalize()}"
    
    if "<title>" in html:
        # Replace present title with the one just defined
        html = re.sub(r"<title>.*?</title>",
                    f"<title>{title}</title>",
                    html,
                    count=1,
                    flags=re.IGNORECASE | re.DOTALL)
    else:
        # Insert title if not present
        html = html.replace(
            "<head>",
            f"<head><title>{title}</title>",
            1
        )

    # Compose final HTML content -- add header and resizing script
    html = html.replace(
        "<body>",
        f"<body>{header_block}{resize_script}",
        1
    )
    
    # Write down static HTML file
    output_file.write_text(html, encoding="utf-8")