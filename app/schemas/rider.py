#app/schemas/rider.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RiderCreate(BaseModel):
    name: str = Field(min_length=1)
    current_lat: float = Field(ge=-90, le=90, description="Latitude must be between -90 and 90")
    current_lon: float = Field(ge=-180, le=180, description="Longitude must be between -180 and 180")


class RiderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    current_lat: float
    current_lon: float
    status: str
    created_at: datetime

