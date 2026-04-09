from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.models import YellowCab

router = APIRouter()


@router.get("/fraud-signals")
def fraud_signals(db: Session = Depends(get_db)):
    return {
        "short_expensive": db.query(func.count())
        .filter(YellowCab.is_short_expensive)
        .scalar(),
        "long_duration_short_distance": db.query(func.count())
        .filter(YellowCab.trip_duration > 1800)
        .filter(YellowCab.trip_distance < 1)
        .scalar(),
        "cash_only": db.query(func.count())
        .filter(YellowCab.payment_type == 2)
        .scalar(),
        "zero_distance_nonzero_fare": db.query(func.count())
        .filter(YellowCab.trip_distance == 0)
        .filter(YellowCab.fare_amount > 0)
        .scalar(),
        "identical_timestamps": db.query(func.count())
        .filter(YellowCab.tpep_pickup_datetime == YellowCab.tpep_dropoff_datetime)
        .scalar(),
    }
