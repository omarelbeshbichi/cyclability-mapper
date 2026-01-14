from fastapi import FastAPI, HTTPException
from.schemas import SegmentNetworkOut
from cmm.services.segments import load_segment_from_id

app = FastAPI()

# Endpoint to fetch segment information from OSM ID (if available)
@app.get("/segments/{osm_id}", response_model = SegmentNetworkOut)
def get_segment(osm_id: str):
    
    segment = load_segment_from_id(osm_id)

    if segment is None:
        raise HTTPException(status_code = 404, detail = "Segment not available in DB")

    return segment