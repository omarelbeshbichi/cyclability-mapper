from pydantic import BaseModel, Field

class SegmentNetworkOut(BaseModel):
    osm_id: str
    street_name: str | None
    bike_infra: str | None
    maxspeed: int | None
    is_oneway: bool | None
    is_lit: bool | None
    surface: str | None
    highway: str | None

class SegmentQuery(BaseModel):
    city: str = Field(min_length = 2)
    min_length: float | None = Field(default = None, ge = 0)