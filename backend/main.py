from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, RootModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.models import YellowCab

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def bucket_query(db: Session, column, start: float, end: float, buckets: int):
    return (
        db.query(
            func.width_bucket(column, start, end, buckets).label("bucket"),
            func.count(),
        )
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )


class Stats(BaseModel):
    rows: int
    avg_fare: float


class TripDistanceStats(BaseModel):
    min: float
    avg: float
    max: float


class PaymentTypeBreakdown(RootModel[dict[str, int]]):
    pass


class HourCount(BaseModel):
    hour: int
    count: int


class LocationCount(BaseModel):
    location: int
    count: int


class TopLocations(BaseModel):
    top_pickups: list[LocationCount]
    top_dropoffs: list[LocationCount]


class TipStats(BaseModel):
    avg_tip: float
    avg_tip_pct: float
    avg_tip_by_hour: list[dict]


class DurationStats(BaseModel):
    min: float
    avg: float
    max: float
    duration_by_hour: list[dict]
    duration_by_distance_bucket: list[dict]


@app.get("/api/stats", response_model=Stats)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(YellowCab.id)).scalar()
    avg_fare = db.query(func.avg(YellowCab.fare_amount)).scalar() or 0
    return Stats(rows=total, avg_fare=float(avg_fare))


@app.get("/api/trip-distance-stats", response_model=TripDistanceStats)
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


@app.get("/api/payment-types", response_model=PaymentTypeBreakdown)
def payment_type_breakdown(db: Session = Depends(get_db)):
    rows = (
        db.query(YellowCab.payment_type, func.count())
        .group_by(YellowCab.payment_type)
        .all()
    )
    return PaymentTypeBreakdown({str(pt): c for pt, c in rows})


@app.get("/api/hourly-distribution", response_model=list[HourCount])
def hourly_distribution(db: Session = Depends(get_db)):
    rows = (
        db.query(YellowCab.hour, func.count())
        .group_by(YellowCab.hour)
        .order_by(YellowCab.hour)
        .all()
    )
    return [HourCount(hour=h, count=c) for h, c in rows]


@app.get("/api/top-locations", response_model=TopLocations)
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

    return TopLocations(
        top_pickups=[LocationCount(location=l, count=c) for l, c in pu],
        top_dropoffs=[LocationCount(location=l, count=c) for l, c in do],
    )


@app.get("/api/tip-stats", response_model=TipStats)
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


@app.get("/api/duration-stats", response_model=DurationStats)
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
        {"hour": h, "pickup": pu, "dropoff": do, "count": c} for h, pu, do, c in rows
    ]


@app.get("/api/fraud-signals")
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


@app.get("/api/outlier-fares")
def outlier_fares(
    limit: int = Query(10, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
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
        .offset(offset)
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
def duplicate_trips(
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
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
        .offset(offset)
        .limit(limit)
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
    rows = bucket_query(db, YellowCab.fare_amount, 0, 40, 3)
    labels = {1: "0-10", 2: "10-20", 3: "20-40", 4: "40+"}
    return [{"bucket": labels.get(b, "unknown"), "count": c} for b, c in rows]


@app.get("/api/distance-buckets")
def distance_buckets(db: Session = Depends(get_db)):
    rows = bucket_query(db, YellowCab.trip_distance, 0, 7, 3)
    labels = {1: "0-1", 2: "1-3", 3: "3-7", 4: "7+"}
    return [{"bucket": labels.get(b, "unknown"), "count": c} for b, c in rows]


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
            "hour": h,
            "avg_distance": float(dist),
            "avg_fare": float(fare),
            "avg_duration": float(dur),
        }
        for h, dist, fare, dur in rows
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
    return [{"pickup": pu, "dropoff": do, "count": c} for pu, do, c in rows]


@app.get("/api/airport-traffic")
def airport_traffic(db: Session = Depends(get_db)):
    airport_ids = {"JFK": 132, "LGA": 138, "EWR": 1}
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
        .filter(YellowCab.trip_duration > 1200)
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
        .filter(YellowCab.payment_type == 2)
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
    return [
        {"name": col.name, "type": str(col.type)} for col in YellowCab.__table__.columns
    ]


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
        return {"status": "ok", "db": "connected", "rows": count}
    except Exception:
        return {"status": "error", "db": "unreachable", "rows": None}
