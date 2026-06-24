from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class OrderCreate(BaseModel):
    customer_id: int
    restaurant_id: int
    value: float = Field(gt=0, description="Order value in INR, must be positive")
    pickup_lat: float = Field(gt=-90, le=90, description="Latitude must be between -90 and 90")
    pickup_lon: float = Field(gt=-180, le=180, description="Longitude must be between -180 and 180")
    drop_lat: float = Field(gt=-90, le=90, description="Latitude must be between -90 and 90")
    drop_lon: float = Field(gt=-180, le=180, description="Longitude must be between -180 and 180")

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    value: float
    status: str
    created_at: datetime
