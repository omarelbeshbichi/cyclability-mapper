from fastapi import FastAPI

from cmm.api.app import app as api_app
from frontend.kepler.app import app as frontend_app

app = FastAPI(title = "cmm system")

app.mount("/api", api_app)
app.mount("/", frontend_app)