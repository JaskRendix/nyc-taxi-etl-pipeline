from fastapi import Depends, FastAPI
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.models import YellowCab

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(YellowCab).count()
    fares = db.query(YellowCab.fare_amount).all()
    avg_fare = sum(f[0] for f in fares) / total if total else 0
    return {"rows": total, "avg_fare": avg_fare}


@app.get("/api/trip-distance-stats")
def trip_distance_stats(db: Session = Depends(get_db)):
    q = db.query(
        func.min(YellowCab.trip_distance),
        func.avg(YellowCab.trip_distance),
        func.max(YellowCab.trip_distance),
    ).one()

    return {
        "min": float(q[0]) if q[0] is not None else 0,
        "avg": float(q[1]) if q[1] is not None else 0,
        "max": float(q[2]) if q[2] is not None else 0,
    }


@app.get("/api/payment-types")
def payment_type_breakdown(db: Session = Depends(get_db)):
    rows = (
        db.query(YellowCab.payment_type, func.count())
        .group_by(YellowCab.payment_type)
        .all()
    )

    return {str(payment_type): count for payment_type, count in rows}


@app.get("/api/hourly-distribution")
def hourly_distribution(db: Session = Depends(get_db)):
    rows = (
        db.query(YellowCab.hour, func.count())
        .group_by(YellowCab.hour)
        .order_by(YellowCab.hour)
        .all()
    )

    return [{"hour": hour, "count": count} for hour, count in rows]


@app.get("/api/top-locations")
def top_locations(limit: int = 10, db: Session = Depends(get_db)):
    pu = (
        db.query(YellowCab.PULocationID, func.count())
        .group_by(YellowCab.PULocationID)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )

    do = (
        db.query(YellowCab.DOLocationID, func.count())
        .group_by(YellowCab.DOLocationID)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )

    return {
        "top_pickups": [{"location": loc, "count": count} for loc, count in pu],
        "top_dropoffs": [{"location": loc, "count": count} for loc, count in do],
    }


@app.get("/api/tip-stats")
def tip_stats(db: Session = Depends(get_db)):
    avg_tip = db.query(func.avg(YellowCab.tip_amount)).scalar() or 0

    tip_pct = (
        db.query(func.avg((YellowCab.tip_amount / YellowCab.fare_amount)))
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

    return {
        "avg_tip": float(avg_tip),
        "avg_tip_pct": float(tip_pct),
        "avg_tip_by_hour": [{"hour": h, "avg_tip": float(v)} for h, v in hourly],
    }


@app.get("/api/duration-stats")
def duration_stats(db: Session = Depends(get_db)):
    q = db.query(
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

    buckets = (
        db.query(
            func.width_bucket(YellowCab.trip_distance, 0, 20, 4).label("bucket"),
            func.avg(YellowCab.trip_duration),
        )
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )

    return {
        "min": float(q[0]) if q[0] else 0,
        "avg": float(q[1]) if q[1] else 0,
        "max": float(q[2]) if q[2] else 0,
        "duration_by_hour": [{"hour": h, "avg_duration": float(v)} for h, v in hourly],
        "duration_by_distance_bucket": [
            {"bucket": b, "avg_duration": float(v)} for b, v in buckets
        ],
    }


@app.get("/api/heatmap-data")
def heatmap_data(db: Session = Depends(get_db)):
    rows = (
        db.query(
            YellowCab.hour,
            YellowCab.PULocationID,
            YellowCab.DOLocationID,
            func.count(),
        )
        .group_by(YellowCab.hour, YellowCab.PULocationID, YellowCab.DOLocationID)
        .all()
    )

    return [
        {
            "hour": hour,
            "pickup": pu,
            "dropoff": do,
            "count": count,
        }
        for hour, pu, do, count in rows
    ]
