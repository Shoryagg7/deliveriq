# app/models/rider.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.core.database import Base


class Rider(Base):
    __tablename__ = "riders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    current_lat = Column(Float, nullable=False)
    current_lon = Column(Float, nullable=False)
    status = Column(String, default="AVAILABLE", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
