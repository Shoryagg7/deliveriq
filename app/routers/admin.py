from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.order import Order
from app.models.rider import Rider

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_orders = db.query(func.count(Order.id)).scalar()
    avg_value = db.query(func.avg(Order.value)).scalar()

    status_rows = (
        db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    )
    orders_by_status = {status: count for status, count in status_rows}

    rider_rows = (
        db.query(Rider.status, func.count(Rider.id)).group_by(Rider.status).all()
    )
    riders_by_status = {status: count for status, count in rider_rows}

    return {
        "total_orders": total_orders,
        "avg_order_value": round(avg_value, 2) if avg_value else 0,
        "orders_by_status": orders_by_status,
        "riders_by_status": riders_by_status,
    }
