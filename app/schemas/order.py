from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    customer_id: int
    restaurant_id: int
    value: float = Field(gt=0, description="Order value in INR, must be positive")
    pickup_lat: float
    pickup_lon: float
    drop_lat: float
    drop_lon: float


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    value: float
    status: str
    created_at: datetime
