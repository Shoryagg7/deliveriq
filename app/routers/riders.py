#app/routers/riders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.rider import Rider
from app.schemas.rider import RiderCreate, RiderResponse

router = APIRouter(prefix="/riders", tags=["riders"])


@router.post("", response_model=RiderResponse, status_code=201)
def create_rider(rider: RiderCreate, db: Session = Depends(get_db)):
    new_rider = Rider(**rider.model_dump())
    db.add(new_rider)
    db.commit()
    db.refresh(new_rider)
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
