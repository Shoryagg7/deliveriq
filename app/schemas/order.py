from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import OrderStatus


class OrderCreate(BaseModel):
    customer_id: int
    restaurant_id: int
    value: float = Field(gt=0, description="Order value in INR, must be positive")
    pickup_lat: float = Field(ge=-90, le=90, description="Latitude must be between -90 and 90")
    pickup_lon: float = Field(ge=-180, le=180, description="Longitude must be between -180 and 180")
    drop_lat: float = Field(ge=-90, le=90, description="Latitude must be between -90 and 90")
    drop_lon: float = Field(ge=-180, le=180, description="Longitude must be between -180 and 180")

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    value: float
    status: OrderStatus
    created_at: datetime
