from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.models import YellowCab

router = APIRouter()


@router.get("/outlier-fares")
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


@router.get("/duplicate-trips")
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


@router.get("/schema")
def schema():
    return [
        {"name": col.name, "type": str(col.type)} for col in YellowCab.__table__.columns
    ]


@router.get("/row-sample")
def row_sample(n: int = 5, db: Session = Depends(get_db)):
    rows = db.query(YellowCab).order_by(func.random()).limit(n).all()
    return [
        {col.name: getattr(row, col.name) for col in YellowCab.__table__.columns}
        for row in rows
    ]
