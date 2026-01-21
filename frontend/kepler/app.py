from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .map import create_map
from cmm.utils.misc import get_project_root
import tempfile

app = FastAPI()

@app.get("/{city_name}", response_class = HTMLResponse)
def serve_map(city_name: str):

    root_path = get_project_root()
    kepler_config_path = root_path  / "frontend" / "kepler" / "kepler_config.json"

    m = create_map(city_name, kepler_config_path)

    # Obtain HTML representation of kepler map (save to temp -> load from temp)
    with tempfile.NamedTemporaryFile(suffix = ".html", delete = False) as f:        
        m.save_to_html(file_name = f.name, read_only = True)
        html_content = f.read().decode("utf-8")

    # Enforce full screen size
    style_fix = """
    <style>
        #kepler-gl__map {
            width: 100vw !important;
            height: 100vh !important;
        }
        body { margin: 0; overflow: hidden; }
    </style>
    """

    html_content = style_fix + html_content

    return HTMLResponse(content = html_content)