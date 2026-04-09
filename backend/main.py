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
