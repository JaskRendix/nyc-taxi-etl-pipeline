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


@app.get("/api/fraud-signals")
def fraud_signals(db: Session = Depends(get_db)):
    short_expensive = (
        db.query(func.count()).filter(YellowCab.is_short_expensive == True).scalar()
    )

    long_duration_short_distance = (
        db.query(func.count())
        .filter(YellowCab.trip_duration > 1800)  # > 30 minutes
        .filter(YellowCab.trip_distance < 1)
        .scalar()
    )

    cash_only = (
        db.query(func.count()).filter(YellowCab.payment_type == 2).scalar()  # 2 = cash
    )

    zero_distance_nonzero_fare = (
        db.query(func.count())
        .filter(YellowCab.trip_distance == 0)
        .filter(YellowCab.fare_amount > 0)
        .scalar()
    )

    identical_timestamps = (
        db.query(func.count())
        .filter(YellowCab.tpep_pickup_datetime == YellowCab.tpep_dropoff_datetime)
        .scalar()
    )

    return {
        "short_expensive": short_expensive,
        "long_duration_short_distance": long_duration_short_distance,
        "cash_only": cash_only,
        "zero_distance_nonzero_fare": zero_distance_nonzero_fare,
        "identical_timestamps": identical_timestamps,
    }


@app.get("/api/outlier-fares")
def outlier_fares(limit: int = 10, db: Session = Depends(get_db)):
    rows = (
        db.query(
            YellowCab.id,
            YellowCab.fare_amount,
            YellowCab.trip_distance,
            (YellowCab.fare_amount / func.nullif(YellowCab.trip_distance, 0)).label(
                "fare_per_mile"
            ),
        )
        .filter(YellowCab.trip_distance > 0)
        .order_by((YellowCab.fare_amount / YellowCab.trip_distance).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "fare": float(r.fare_amount),
            "distance": float(r.trip_distance),
            "fare_per_mile": float(r.fare_per_mile),
        }
        for r in rows
    ]


@app.get("/api/duplicate-trips")
def duplicate_trips(db: Session = Depends(get_db)):
    rows = (
        db.query(
            YellowCab.tpep_pickup_datetime,
            YellowCab.tpep_dropoff_datetime,
            YellowCab.PULocationID,
            YellowCab.DOLocationID,
            YellowCab.passenger_count,
            func.count().label("count"),
        )
        .group_by(
            YellowCab.tpep_pickup_datetime,
            YellowCab.tpep_dropoff_datetime,
            YellowCab.PULocationID,
            YellowCab.DOLocationID,
            YellowCab.passenger_count,
        )
        .having(func.count() > 1)
        .all()
    )

    return [
        {
            "pickup": str(pu),
            "dropoff": str(do),
            "pulocation": pu_loc,
            "dolocation": do_loc,
            "passengers": pax,
            "count": count,
        }
        for pu, do, pu_loc, do_loc, pax, count in rows
    ]


@app.get("/api/fare-buckets")
def fare_buckets(db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.width_bucket(YellowCab.fare_amount, 0, 40, 3).label("bucket"),
            func.count(),
        )
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )

    # Map bucket numbers to human-readable ranges
    bucket_labels = {
        1: "0-10",
        2: "10-20",
        3: "20-40",
        4: "40+",
    }

    return [
        {"bucket": bucket_labels.get(b, "unknown"), "count": count} for b, count in rows
    ]


@app.get("/api/distance-buckets")
def distance_buckets(db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.width_bucket(YellowCab.trip_distance, 0, 7, 3).label("bucket"),
            func.count(),
        )
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )

    bucket_labels = {
        1: "0-1",
        2: "1-3",
        3: "3-7",
        4: "7+",
    }

    return [
        {"bucket": bucket_labels.get(b, "unknown"), "count": count} for b, count in rows
    ]


@app.get("/api/cluster-hints")
def cluster_hints(db: Session = Depends(get_db)):
    rows = (
        db.query(
            YellowCab.hour,
            func.avg(YellowCab.trip_distance),
            func.avg(YellowCab.fare_amount),
            func.avg(YellowCab.trip_duration),
        )
        .group_by(YellowCab.hour)
        .order_by(YellowCab.hour)
        .all()
    )

    return [
        {
            "hour": hour,
            "avg_distance": float(dist),
            "avg_fare": float(fare),
            "avg_duration": float(dur),
        }
        for hour, dist, fare, dur in rows
    ]


@app.get("/api/location-pairs")
def location_pairs(limit: int = 10, db: Session = Depends(get_db)):
    rows = (
        db.query(
            YellowCab.PULocationID,
            YellowCab.DOLocationID,
            func.count().label("count"),
        )
        .group_by(YellowCab.PULocationID, YellowCab.DOLocationID)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "pickup": pu,
            "dropoff": do,
            "count": count,
        }
        for pu, do, count in rows
    ]


@app.get("/api/airport-traffic")
def airport_traffic(db: Session = Depends(get_db)):
    airport_ids = {
        "JFK": 132,
        "LGA": 138,
        "EWR": 1,
    }

    results = {}

    for name, loc_id in airport_ids.items():
        count_pu = (
            db.query(func.count()).filter(YellowCab.PULocationID == loc_id).scalar()
        )

        count_do = (
            db.query(func.count()).filter(YellowCab.DOLocationID == loc_id).scalar()
        )

        hourly = (
            db.query(YellowCab.hour, func.count())
            .filter(
                (YellowCab.PULocationID == loc_id) | (YellowCab.DOLocationID == loc_id)
            )
            .group_by(YellowCab.hour)
            .order_by(YellowCab.hour)
            .all()
        )

        results[name] = {
            "pickup_count": count_pu,
            "dropoff_count": count_do,
            "hourly_distribution": [{"hour": h, "count": c} for h, c in hourly],
        }

    return results


@app.get("/api/rush-hour-squeeze")
def rush_hour_squeeze(db: Session = Depends(get_db)):
    rows = (
        db.query(
            YellowCab.id,
            YellowCab.trip_distance,
            YellowCab.trip_duration,
            YellowCab.fare_amount,
            YellowCab.hour,
        )
        .filter(YellowCab.trip_distance < 1)
        .filter(YellowCab.trip_duration > 1200)  # > 20 minutes
        .filter(YellowCab.fare_amount > 20)
        .all()
    )

    return [
        {
            "id": r.id,
            "distance": float(r.trip_distance),
            "duration": float(r.trip_duration),
            "fare": float(r.fare_amount),
            "hour": r.hour,
        }
        for r in rows
    ]


@app.get("/api/late-night-surges")
def late_night_surges(db: Session = Depends(get_db)):
    rows = (
        db.query(
            YellowCab.id,
            YellowCab.trip_distance,
            YellowCab.fare_amount,
            YellowCab.payment_type,
            YellowCab.hour,
        )
        .filter(YellowCab.hour.between(1, 4))
        .filter(YellowCab.trip_distance > 5)
        .filter(YellowCab.fare_amount > 30)
        .filter(YellowCab.payment_type == 2)  # cash
        .all()
    )

    return [
        {
            "id": r.id,
            "distance": float(r.trip_distance),
            "fare": float(r.fare_amount),
            "payment_type": r.payment_type,
            "hour": r.hour,
        }
        for r in rows
    ]


@app.get("/api/too-good-to-be-true")
def too_good_to_be_true(db: Session = Depends(get_db)):
    rows = (
        db.query(
            YellowCab.id,
            YellowCab.trip_distance,
            YellowCab.fare_amount,
            YellowCab.hour,
        )
        .filter(YellowCab.trip_distance > 10)
        .filter(YellowCab.fare_amount < 10)
        .all()
    )

    return [
        {
            "id": r.id,
            "distance": float(r.trip_distance),
            "fare": float(r.fare_amount),
            "hour": r.hour,
        }
        for r in rows
    ]


@app.get("/api/schema")
def schema():
    cols = []
    for col in YellowCab.__table__.columns:
        cols.append({"name": col.name, "type": str(col.type)})
    return cols


@app.get("/api/row-sample")
def row_sample(n: int = 5, db: Session = Depends(get_db)):
    rows = db.query(YellowCab).order_by(func.random()).limit(n).all()

    return [
        {col.name: getattr(row, col.name) for col in YellowCab.__table__.columns}
        for row in rows
    ]


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        count = db.query(func.count(YellowCab.id)).scalar()
        return {
            "status": "ok",
            "db": "connected",
            "rows": count,
        }
    except Exception:
        return {
            "status": "error",
            "db": "unreachable",
            "rows": None,
        }
