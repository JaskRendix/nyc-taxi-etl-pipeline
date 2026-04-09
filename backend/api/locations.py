from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.schemas import LocationCount, TopLocations
from backend.core.db import get_db
from backend.models import YellowCab

router = APIRouter()


@router.get("/top-locations", response_model=TopLocations)
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


@router.get("/heatmap-data")
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


@router.get("/location-pairs")
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


@router.get("/airport-traffic")
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


@router.get("/cluster-hints")
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


@router.get("/rush-hour-squeeze")
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


@router.get("/late-night-surges")
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


@router.get("/too-good-to-be-true")
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
