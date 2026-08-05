from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.schemas import DuplicateTripItem, OutlierFareItem, SchemaColumnItem
from backend.core.db import get_db
from backend.models import YellowCab

router = APIRouter()


@router.get("/outlier-fares", response_model=list[OutlierFareItem])
def outlier_fares(
    limit: int = Query(default=10, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[OutlierFareItem]:
    """Retrieve trips with the highest fare-per-mile ratios."""
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


@router.get("/duplicate-trips", response_model=list[DuplicateTripItem])
def duplicate_trips(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[DuplicateTripItem]:
    """Retrieve groups of identical trips appearing multiple times in the dataset."""
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


@router.get("/schema", response_model=list[SchemaColumnItem])
def schema() -> list[SchemaColumnItem]:
    """Retrieve column names and data types for the YellowCab schema."""
    return [
        {"name": col.name, "type": str(col.type)} for col in YellowCab.__table__.columns
    ]


@router.get("/row-sample", response_model=list[dict[str, Any]])
def row_sample(
    n: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve a random sample of rows from the dataset."""
    rows = db.query(YellowCab).order_by(func.random()).limit(n).all()
    return [
        {col.name: getattr(row, col.name) for col in YellowCab.__table__.columns}
        for row in rows
    ]
