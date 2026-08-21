from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import OrderStatus


class OrderCreate(BaseModel):
    # NO customer_id (G02). It used to be a request-body field, so any caller
    # could place an order as anyone. Identity comes from the verified token in
    # the router — a field the server must check against the token is a field
    # the client should not be sending.
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
    # Who it was dispatched to; None while PENDING. The console renders this as
    # a "rider N" badge — without it that badge was dead code and an assigned
    # order looked identical to an unassigned one.
    rider_id: int | None = None
