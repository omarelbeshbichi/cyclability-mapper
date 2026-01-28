from fastapi import APIRouter, HTTPException
from city_metrics.api.schemas.segment import SegmentNetworkOut
from city_metrics.services.segments import load_segment_from_id


router = APIRouter(prefix = "/segments", tags = ["segments"])

@router.get("/{city_name}/{osm_id}", response_model = SegmentNetworkOut)
def get_segment(city_name: str, osm_id: str):
    
    segment = load_segment_from_id(city_name, osm_id)

    if segment is None:
        raise HTTPException(status_code = 404, detail = "Segment not available in DB")

    return segment
