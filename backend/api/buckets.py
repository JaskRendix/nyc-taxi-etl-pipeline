from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.utils import bucket_query
from backend.models import YellowCab

router = APIRouter()


@router.get("/fare-buckets")
def fare_buckets(db: Session = Depends(get_db)):
    rows = bucket_query(db, YellowCab.fare_amount, 0, 40, 3)
    labels = {1: "0-10", 2: "10-20", 3: "20-40", 4: "40+"}
    return [{"bucket": labels.get(b, "unknown"), "count": c} for b, c in rows]


@router.get("/distance-buckets")
def distance_buckets(db: Session = Depends(get_db)):
    rows = bucket_query(db, YellowCab.trip_distance, 0, 7, 3)
    labels = {1: "0-1", 2: "1-3", 3: "3-7", 4: "7+"}
    return [{"bucket": labels.get(b, "unknown"), "count": c} for b, c in rows]
