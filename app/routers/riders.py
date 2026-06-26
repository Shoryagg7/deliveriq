#app/routers/riders.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.rider import Rider
from app.schemas.rider import RiderCreate, RiderResponse
from app.services.geohash_service import add_rider, select_rider, update_rider_location

router = APIRouter(prefix="/riders", tags=["riders"])


@router.post("", response_model=RiderResponse, status_code=201)
def create_rider(rider: RiderCreate, db: Session = Depends(get_db)):
    new_rider = Rider(**rider.model_dump())
    db.add(new_rider)
    db.commit()
    db.refresh(new_rider)  # ← need the DB-generated id first
    add_rider(new_rider.id, new_rider.current_lat, new_rider.current_lon) # type: ignore
    return new_rider


@router.get("/{rider_id}", response_model=RiderResponse)
def get_rider(rider_id: int, db: Session = Depends(get_db)):
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(404, "Rider not found")
    return rider


@router.get("", response_model=list[RiderResponse])
def list_riders(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Rider)
    if status:
        query = query.filter(Rider.status == status)
    return query.all()

class MatchRequest(BaseModel):
    lat: float
    lon: float


@router.post("/match")
def match_rider(req: MatchRequest, db: Session = Depends(get_db)):
    rider_id = select_rider(req.lat, req.lon)
    if rider_id is None:
        raise HTTPException(404, "No available rider nearby")
    return {"assigned_rider_id": rider_id}

class LocationUpdate(BaseModel):
    lat: float
    lon: float


@router.patch("/{rider_id}/location")
def update_location(rider_id: int, loc: LocationUpdate, db: Session = Depends(get_db)):
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(404, "Rider not found")
    rider.current_lat, rider.current_lon = loc.lat, loc.lon  # type: ignore # Postgres = truth
    db.commit()
    update_rider_location(rider_id, loc.lat, loc.lon)  # Redis index follows
    return {"status": "updated", "rider_id": rider_id}
