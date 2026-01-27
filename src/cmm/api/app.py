from fastapi import FastAPI
from cmm.api.routes.segments import router as segments_router


app = FastAPI(title = "cmm api")

# Include segment router to API
app.include_router(segments_router)