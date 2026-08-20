# app/routers/riders.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import assert_may_move_rider, get_current_user, require_ops
from app.core.exceptions import RiderNotFound
from app.models.rider import Rider
from app.models.user import User
from app.schemas.rider import RiderCreate, RiderResponse
from app.services.geohash_service import add_rider, update_rider_location

router = APIRouter(prefix="/riders", tags=["riders"])


@router.post("", response_model=RiderResponse, status_code=201)
def create_rider(
    rider: RiderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_ops),
):
    """OPS ONLY — onboarding a courier is an operator action. Left open,
    anyone could inject riders into the dispatch pool."""
    new_rider = Rider(**rider.model_dump())
    db.add(new_rider)
    db.commit()
    db.refresh(new_rider)  # ← need the DB-generated id first
    add_rider(new_rider.id, new_rider.current_lat, new_rider.current_lon)  # type: ignore
    return new_rider


@router.get("/{rider_id}", response_model=RiderResponse)
def get_rider(
    rider_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ops, or the rider themselves (G03).

    Reuses the location guard: "who may read this rider" and "who may move this
    rider" have the same answer, and two rules that must agree are better as one
    rule.
    """
    assert_may_move_rider(user, rider_id)
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise RiderNotFound(f"Rider {rider_id} not found")
    return rider


@router.get("", response_model=list[RiderResponse])
def list_riders(
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_ops),
):
    """OPS ONLY (G03). The full roster with live positions is fleet data — it
    was readable by anyone, which is a staff-location leak, not a listing."""
    query = db.query(Rider)
    if status:
        query = query.filter(Rider.status == status)
    return query.all()


class LocationUpdate(BaseModel):
    lat: float
    lon: float


@router.patch("/{rider_id}/location")
def update_location(
    rider_id: int,
    loc: LocationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """A rider moves themselves; ops may move anyone; a customer never.

    This writes through to the Redis geohash index, which is what dispatch
    matches on — so it is a dispatch-integrity endpoint, not a profile update.
    Authorise BEFORE the existence check, so an unauthorised caller cannot use
    the 404-vs-403 difference to enumerate the fleet.
    """
    assert_may_move_rider(user, rider_id)

    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise RiderNotFound(f"Rider {rider_id} not found")
    rider.current_lat, rider.current_lon = loc.lat, loc.lon  # type: ignore # Postgres = truth
    db.commit()
    update_rider_location(rider_id, loc.lat, loc.lon)  # Redis index follows
    return {"status": "updated", "rider_id": rider_id}
