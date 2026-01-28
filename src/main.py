from fastapi import FastAPI

from city_metrics.api.app import app as api_app
from frontend.kepler.app import app as frontend_app
from frontend.figures.app import app as figures_app

app = FastAPI(title = "city_metrics system")

app.mount("/api", api_app)
app.mount("/maps", frontend_app)
app.mount("/figures", figures_app)