from fastapi import FastAPI
from city_metrics.api.routes.segments import router as segments_router


app = FastAPI(title = "city_metrics api")

# Include segment router to API
app.include_router(segments_router)