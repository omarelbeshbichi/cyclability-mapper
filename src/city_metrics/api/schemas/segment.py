from pydantic import BaseModel, Field
from typing import Optional, Dict


class SegmentNetworkOut(BaseModel):
    osm_id: str
    street_name: Optional[str]
    bike_infra: Optional[str]
    maxspeed: Optional[int]
    is_oneway: Optional[bool]
    is_lit: Optional[bool]
    surface: Optional[str]
    highway: Optional[str]
    total_score: Optional[float]
    missing_features: Optional[Dict[str, bool]]
    metric_features_scores: Optional[Dict[str, float]]
    metric_version: Optional[str]

class SegmentQuery(BaseModel):
    city: str = Field(min_length = 2)
    min_length: float | None = Field(default = None, ge = 0)