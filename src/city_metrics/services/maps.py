import logging
from frontend.kepler.map import create_map
from pathlib import Path
import re
import os
from frontend.figures.settings import settings
import boto3
from sqlalchemy import create_engine, text
from datetime import timezone
from io import BytesIO
from frontend.figures.figures import create_city_metrics_scatter_plot

def get_global_last_updated() -> str:
    """
    Fetch latest created_at timestamp across all cities.
    Returns formatted UTC string.
    """

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/db"
    )

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT MAX(created_at)
                FROM city_metrics
            """)
        ).scalar()

    engine.dispose()

    if result is None:
        return "Unknown"

    result = result.astimezone(timezone.utc)
    return result.strftime("%Y-%m-%d %H:%M UTC")

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
    if settings.storage_backend == "s3":
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
            background:white;
            border-radius:4px;
            padding:4px;
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
            <img src="https://upload.wikimedia.org/wikipedia/commons/9/91/Octicons-mark-github.svg">
            </a>
        </div>
        """
    elif settings.storage_backend == "local":
           
           last_updated = get_global_last_updated()

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
                height: 64px;
                background: linear-gradient(90deg, #0e0e0e, #1a1a1a);
                color: #fff;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 28px;
                box-sizing: border-box;
            }}

            .app-title {{
                font-size: 16px;
                font-weight: 500;
                letter-spacing: 0.3px;
            }}

            .app-subtitle {{
                font-size: 12px;
                color: #aaa;
                margin-top: 4px;
            }}

            .badge-group {{
                display: flex;
                align-items: center;
                gap: 18px;
            }}

            .badge {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                color: #eaeaea;
                opacity: 0.85;
            }}

            .badge img {{
                width: 20px;
                height: 20px;
                object-fit: contain;
                background:white;
                border-radius:4px;
                padding:4px;
            }}

            .github-link img {{
                width: 20px;
                height: 20px;
                object-fit: contain;
                background:white;
                border-radius:4px;
                padding:4px;
            }}

            .github-link {{
                display: flex;
                align-items: center;
                gap: 6px;
                text-decoration: none;
                color: #fff;
                opacity: 0.85;
                font-size: 13px;
            }}

            .github-link:hover {{
                opacity: 1.0;
            }}

            </style>

            <div class="app-header">
                <div>
                    <div class="app-title">
                        Cyclability Mapper - {city_name.capitalize()}
                    </div>
                    <div class="app-subtitle">
                        Last updated: {last_updated}
                    </div>
                </div>

                <div class="badge-group">

                    <div class="badge">
                        <img src="https://logo.svgcdn.com/logos/aws.png">
                        Deployed on AWS
                    </div>

                    <div class="badge">
                        <img src="https://icon.icepanel.io/Technology/svg/Apache-Airflow.svg">
                        Updated weekly via Airflow
                    </div>

                    <a class="github-link"
                    href="https://github.com/omarelbeshbichi/cyclability-mapper"
                    target="_blank">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/9/91/Octicons-mark-github.svg">
                        View Source
                    </a>

                </div>
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
    
    if settings.storage_backend == "local":
        # Write down static HTML file
        output_file.write_text(html, encoding="utf-8")
        logging.info("Map stored locally: %s", output_file)

    elif settings.storage_backend == "s3":
        
        s3_client = boto3.client("s3")
        s3_key = f"{settings.s3_prefix}/{city_name}.html"

        s3_client.upload_fileobj(
            BytesIO(html.encode("utf-8")),
            settings.s3_bucket,
            s3_key,
            ExtraArgs={"ContentType": "text/html"}
        )

        logging.info(
            "Map uploaded to S3: s3://%s/%s",
            settings.s3_bucket,
            s3_key
        )

        # Delete local file after successful upload
        if output_file.exists():
            output_file.unlink()
            logging.info("Local file deleted: %s", output_file)

    else:
        raise ValueError("Invalid storage backend")
    
def create_static_metrics_scatter( 
                      output_dir: Path,
                      overwrite: bool = True) -> None:
    """
    Generate static HTML Kepler.gl-based map and saves it in output directory.

    Parameters
    ----------
    output_dir: Path
        Path to the output directory where static HTML map will be saved
    overwrite: bool
        Bool flag to determine whether already existing data should be overwritten
    """
    logging.info("Generating metrics scatter figure")
    # Create metrics scatter figure
    metrics_scatter_figure = create_city_metrics_scatter_plot()

    # Static metrics scatter name
    output_file = output_dir / f"metrics_scatter.html"

    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"Static map already exists: {output_file}. "
            "Use --overwrite to regenerate."
        )

    # Script used to resize figure to viewport
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
    if settings.storage_backend == "local":
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
            background:white;
            border-radius:4px;
            padding:4px;
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
                Cyclability Mapper - Metrics Scatter
            </div>
            <a class="github-link"
            href="https://github.com/omarelbeshbichi/cyclability-mapper"
            target="_blank">
            <span class="github-label">View source</span>
            <img src="https://upload.wikimedia.org/wikipedia/commons/9/91/Octicons-mark-github.svg">
            </a>
        </div>
        """
    elif settings.storage_backend == "s3":

        last_updated = get_global_last_updated()

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
                height: 64px;
                background: linear-gradient(90deg, #0e0e0e, #1a1a1a);
                color: #fff;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 28px;
                box-sizing: border-box;
            }}

            .app-title {{
                font-size: 16px;
                font-weight: 500;
                letter-spacing: 0.3px;
            }}

            .app-subtitle {{
                font-size: 12px;
                color: #aaa;
                margin-top: 4px;
            }}

            .badge-group {{
                display: flex;
                align-items: center;
                gap: 18px;
            }}

            .badge {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                color: #eaeaea;
                opacity: 0.85;
            }}

            .badge img {{
                width: 20px;
                height: 20px;
                object-fit: contain;
                background:white;
                border-radius:4px;
                padding:4px;
            }}

            .github-link img {{
                width: 20px;
                height: 20px;
                object-fit: contain;
                background:white;
                border-radius:4px;
                padding:4px;
            }}

            .github-link {{
                display: flex;
                align-items: center;
                gap: 6px;
                text-decoration: none;
                color: #fff;
                opacity: 0.85;
                font-size: 13px;
            }}

            .github-link:hover {{
                opacity: 1.0;
            }}

            </style>

            <div class="app-header">
                <div>
                    <div class="app-title">
                        Cyclability Mapper - Metrics Scatter
                    </div>
                    <div class="app-subtitle">
                        Last updated: {last_updated}
                    </div>
                </div>

                <div class="badge-group">

                    <div class="badge">
                        <img src="https://logo.svgcdn.com/logos/aws.png">
                        Deployed on AWS
                    </div>

                    <div class="badge">
                        <img src="https://icon.icepanel.io/Technology/svg/Apache-Airflow.svg">
                        Updated weekly via Airflow
                    </div>

                    <a class="github-link"
                    href="https://github.com/omarelbeshbichi/cyclability-mapper"
                    target="_blank">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/9/91/Octicons-mark-github.svg">
                        View Source
                    </a>

                </div>
            </div>
            """
    

    metrics_scatter_figure.write_html(
        str(output_file),
        full_html=True,
        include_plotlyjs="cdn"
    )
    
    # Retrieve HTML content
    html = output_file.read_text(encoding="utf-8")

    # Define page text
    title = f"Cyclability Mapper - Metrics Scatter"
    
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
    
    if settings.storage_backend == "local":
        # Write down static HTML file
        output_file.write_text(html, encoding="utf-8")
        logging.info("Metrics scatter stored locally: %s", output_file)

    elif settings.storage_backend == "s3":
        
        s3_client = boto3.client("s3")
        s3_key = f"{settings.s3_prefix}/metrics_scatter.html"

        s3_client.upload_fileobj(
            BytesIO(html.encode("utf-8")),
            settings.s3_bucket,
            s3_key,
            ExtraArgs={"ContentType": "text/html"}
        )

        logging.info(
            "Metrics scatter uploaded to S3: s3://%s/%s",
            settings.s3_bucket,
            s3_key
        )

        # Delete local file after successful upload
        if output_file.exists():
            output_file.unlink()
            logging.info("Local file deleted: %s", output_file)

    else:
        raise ValueError("Invalid storage backend")