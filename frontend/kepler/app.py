from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .helper import get_map_response

app = FastAPI()

@app.get("/{city_name}", response_class = HTMLResponse)
def serve_map(city_name: str):

    return get_map_response(city_name)