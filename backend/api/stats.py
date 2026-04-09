from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.schemas import DurationStats, Stats, TipStats, TripDistanceStats
from backend.core.db import get_db
from backend.core.utils import bucket_query
from backend.models import YellowCab

router = APIRouter()


@router.get("/stats", response_model=Stats)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(YellowCab.id)).scalar()
    avg_fare = db.query(func.avg(YellowCab.fare_amount)).scalar() or 0
    return Stats(rows=total, avg_fare=float(avg_fare))


@router.get("/trip-distance-stats", response_model=TripDistanceStats)
def trip_distance_stats(db: Session = Depends(get_db)):
    mn, avg, mx = db.query(
        func.min(YellowCab.trip_distance),
        func.avg(YellowCab.trip_distance),
        func.max(YellowCab.trip_distance),
    ).one()

    return TripDistanceStats(
        min=float(mn or 0),
        avg=float(avg or 0),
        max=float(mx or 0),
    )


@router.get("/payment-types")
def payment_type_breakdown(db: Session = Depends(get_db)):
    rows = (
        db.query(YellowCab.payment_type, func.count())
        .group_by(YellowCab.payment_type)
        .all()
    )
    return {str(pt): c for pt, c in rows}


@router.get("/hourly-distribution")
def hourly_distribution(db: Session = Depends(get_db)):
    rows = (
        db.query(YellowCab.hour, func.count())
        .group_by(YellowCab.hour)
        .order_by(YellowCab.hour)
        .all()
    )
    return [{"hour": h, "count": c} for h, c in rows]


@router.get("/tip-stats", response_model=TipStats)
def tip_stats(db: Session = Depends(get_db)):
    avg_tip = db.query(func.avg(YellowCab.tip_amount)).scalar() or 0
    avg_pct = (
        db.query(func.avg(YellowCab.tip_amount / YellowCab.fare_amount))
        .filter(YellowCab.fare_amount > 0)
        .scalar()
        or 0
    )

    hourly = (
        db.query(YellowCab.hour, func.avg(YellowCab.tip_amount))
        .group_by(YellowCab.hour)
        .order_by(YellowCab.hour)
        .all()
    )

    return TipStats(
        avg_tip=float(avg_tip),
        avg_tip_pct=float(avg_pct),
        avg_tip_by_hour=[{"hour": h, "avg_tip": float(v)} for h, v in hourly],
    )


@router.get("/duration-stats", response_model=DurationStats)
def duration_stats(db: Session = Depends(get_db)):
    mn, avg, mx = db.query(
        func.min(YellowCab.trip_duration),
        func.avg(YellowCab.trip_duration),
        func.max(YellowCab.trip_duration),
    ).one()

    hourly = (
        db.query(YellowCab.hour, func.avg(YellowCab.trip_duration))
        .group_by(YellowCab.hour)
        .order_by(YellowCab.hour)
        .all()
    )

    buckets = bucket_query(db, YellowCab.trip_distance, 0, 20, 4)

    return DurationStats(
        min=float(mn or 0),
        avg=float(avg or 0),
        max=float(mx or 0),
        duration_by_hour=[{"hour": h, "avg_duration": float(v)} for h, v in hourly],
        duration_by_distance_bucket=[
            {"bucket": b, "avg_duration": float(v)} for b, v in buckets
        ],
    )
