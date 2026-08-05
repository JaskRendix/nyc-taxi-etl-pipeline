from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.api.schemas import (
    DayOfWeekTrendItem,
    DurationStats,
    HourlyDistributionItem,
    PaymentTypeBreakdown,
    ShiftAnalysisItem,
    Stats,
    TipStats,
    TripDistanceStats,
)
from backend.core.db import get_db
from backend.core.utils import bucket_query
from backend.models import YellowCab

router = APIRouter()


@router.get("/stats", response_model=Stats)
def get_stats(db: Session = Depends(get_db)) -> Stats:
    """Retrieve overall row counts and average fare statistics."""
    total = db.query(func.count(YellowCab.id)).scalar() or 0
    avg_fare = db.query(func.avg(YellowCab.fare_amount)).scalar() or 0
    return Stats(rows=total, avg_fare=float(avg_fare))


@router.get("/trip-distance-stats", response_model=TripDistanceStats)
def trip_distance_stats(db: Session = Depends(get_db)) -> TripDistanceStats:
    """Retrieve minimum, average, and maximum trip distance metrics."""
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


@router.get("/payment-types", response_model=PaymentTypeBreakdown)
def payment_type_breakdown(db: Session = Depends(get_db)) -> PaymentTypeBreakdown:
    """Retrieve a breakdown of trip counts grouped by payment type."""
    rows = (
        db.query(YellowCab.payment_type, func.count())
        .group_by(YellowCab.payment_type)
        .all()
    )
    return PaymentTypeBreakdown({str(pt): c for pt, c in rows})


@router.get("/hourly-distribution", response_model=list[HourlyDistributionItem])
def hourly_distribution(db: Session = Depends(get_db)) -> list[HourlyDistributionItem]:
    """Retrieve trip counts distributed across hours of the day."""
    rows = (
        db.query(YellowCab.hour, func.count())
        .group_by(YellowCab.hour)
        .order_by(YellowCab.hour)
        .all()
    )
    return [{"hour": h, "count": c} for h, c in rows]


@router.get("/day-of-week-trends", response_model=list[DayOfWeekTrendItem])
def day_of_week_trends(db: Session = Depends(get_db)) -> list[DayOfWeekTrendItem]:
    """Retrieve trip volume, average fare, and average duration distributed across days of the week."""
    dow_expr = func.extract("dow", YellowCab.tpep_pickup_datetime)
    rows = (
        db.query(
            dow_expr.label("dow"),
            func.count().label("count"),
            func.avg(YellowCab.fare_amount).label("avg_fare"),
            func.avg(YellowCab.trip_duration).label("avg_duration"),
        )
        .group_by(dow_expr)
        .order_by(dow_expr)
        .all()
    )
    return [
        {
            "day_of_week": int(dow) if dow is not None else 0,
            "count": c,
            "avg_fare": float(af or 0),
            "avg_duration": float(ad or 0),
        }
        for dow, c, af, ad in rows
    ]


@router.get("/shift-analysis", response_model=list[ShiftAnalysisItem])
def shift_analysis(db: Session = Depends(get_db)) -> list[ShiftAnalysisItem]:
    """Retrieve performance metrics grouped by standard driver shifts (Morning Rush, Midday, Evening Rush, Graveyard)."""
    shift_case = case(
        (
            (YellowCab.hour >= 6) & (YellowCab.hour < 10),
            "Morning Rush",
        ),
        (
            (YellowCab.hour >= 10) & (YellowCab.hour < 16),
            "Midday",
        ),
        (
            (YellowCab.hour >= 16) & (YellowCab.hour < 20),
            "Evening Rush",
        ),
        else_="Graveyard",
    ).label("shift")

    rows = (
        db.query(
            shift_case,
            func.count().label("count"),
            func.avg(YellowCab.fare_amount).label("avg_fare"),
            func.avg(YellowCab.tip_amount).label("avg_tip"),
            func.avg(YellowCab.trip_duration).label("avg_duration"),
        )
        .group_by(shift_case)
        .all()
    )

    return [
        {
            "shift": s,
            "count": c,
            "avg_fare": float(af or 0),
            "avg_tip": float(at or 0),
            "avg_duration": float(ad or 0),
        }
        for s, c, af, at, ad in rows
    ]


@router.get("/tip-stats", response_model=TipStats)
def tip_stats(db: Session = Depends(get_db)) -> TipStats:
    """Retrieve average tip amounts, percentages, and hourly breakdowns."""
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
def duration_stats(db: Session = Depends(get_db)) -> DurationStats:
    """Retrieve minimum, average, and maximum trip duration stats alongside hourly and distance buckets."""
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
