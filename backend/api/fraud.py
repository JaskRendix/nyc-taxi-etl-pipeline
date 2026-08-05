from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.api.schemas import (
    FareDistanceAnomalyItem,
    FraudSignalsResponse,
    RouteCircuitousnessItem,
    TipOutlierItem,
)
from backend.core.db import get_db
from backend.models import YellowCab

router = APIRouter()


@router.get("/fraud-signals", response_model=FraudSignalsResponse)
def fraud_signals(
    db: Session = Depends(get_db),
    start_date: datetime | None = Query(
        default=None, description="Filter trips starting from this datetime"
    ),
    end_date: datetime | None = Query(
        default=None, description="Filter trips ending before this datetime"
    ),
) -> dict[str, Any]:
    """Retrieve aggregate counts and percentage ratios for various taxi trip fraud and anomaly signals."""
    query = db.query(func.count().label("total_trips"))

    if start_date:
        query = query.filter(YellowCab.tpep_pickup_datetime >= start_date)
    if end_date:
        query = query.filter(YellowCab.tpep_dropoff_datetime <= end_date)

    result = query.with_entities(
        func.count().label("total_trips"),
        func.sum(case((YellowCab.is_short_expensive == True, 1), else_=0)).label(
            "short_expensive"
        ),
        func.sum(
            case(
                ((YellowCab.trip_duration > 1800) & (YellowCab.trip_distance < 1), 1),
                else_=0,
            )
        ).label("long_duration_short_distance"),
        func.sum(case((YellowCab.payment_type == 2, 1), else_=0)).label("cash_only"),
        func.sum(
            case(
                ((YellowCab.trip_distance == 0) & (YellowCab.fare_amount > 0), 1),
                else_=0,
            )
        ).label("zero_distance_nonzero_fare"),
        func.sum(
            case(
                (
                    (YellowCab.tpep_pickup_datetime == YellowCab.tpep_dropoff_datetime),
                    1,
                ),
                else_=0,
            )
        ).label("identical_timestamps"),
        func.sum(
            case(
                (
                    (YellowCab.passenger_count == 0)
                    | (YellowCab.passenger_count.is_(None)),
                    1,
                ),
                else_=0,
            )
        ).label("no_passenger_count"),
        func.sum(
            case(((YellowCab.tip_amount > (YellowCab.fare_amount * 0.5)), 1), else_=0)
        ).label("high_tip_percentage"),
        func.sum(case((YellowCab.fare_amount < 0, 1), else_=0)).label("negative_fare"),
        func.sum(
            case(
                (
                    (YellowCab.trip_duration > 0)
                    & (
                        (YellowCab.trip_distance / (YellowCab.trip_duration / 3600))
                        > 100
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("impossible_speed"),
        func.sum(case((YellowCab.total_amount > 500, 1), else_=0)).label(
            "very_high_total_amount"
        ),
    ).one()

    data = dict(result._mapping)
    total = data.get("total_trips", 0) or 1  # prevent division by zero

    # Flatten response to match test expectations (keys at top-level alongside signals)
    response: dict[str, Any] = {
        "total_trips": data.get("total_trips", 0),
        "signals": {
            key: {
                "count": count,
                "percentage": round((count / total) * 100, 4) if count else 0.0,
            }
            for key, count in data.items()
            if key != "total_trips"
        },
    }

    # Expose individual keys at root level for backward compatibility with existing tests
    for key, count in data.items():
        if key != "total_trips":
            response[key] = count

    return response


@router.get("/tip-outliers", response_model=list[TipOutlierItem])
def tip_outliers(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Flag trips where the tip amount is an statistical outlier based on high fare/distance brackets."""
    avg_tip = db.query(func.avg(YellowCab.tip_amount)).scalar() or 0
    std_tip = db.query(func.stddev(YellowCab.tip_amount)).scalar() or 1
    threshold = float(avg_tip) + (3 * float(std_tip))

    rows = (
        db.query(
            YellowCab.id,
            YellowCab.tip_amount,
            YellowCab.fare_amount,
            YellowCab.trip_distance,
        )
        .filter(YellowCab.tip_amount > threshold)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "tip_amount": float(r.tip_amount),
            "fare_amount": float(r.fare_amount),
            "trip_distance": float(r.trip_distance),
            "threshold_used": threshold,
        }
        for r in rows
    ]


@router.get("/route-circuitousness", response_model=list[RouteCircuitousnessItem])
def route_circuitousness(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Flag potential long-hauling fraud where actual distance heavily exceeds standard expectations for short fares."""
    rows = (
        db.query(
            YellowCab.id,
            YellowCab.trip_distance,
            YellowCab.fare_amount,
            YellowCab.trip_duration,
        )
        .filter(YellowCab.trip_distance > 15)
        .filter(YellowCab.fare_amount < 20)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "trip_distance": float(r.trip_distance),
            "fare_amount": float(r.fare_amount),
            "trip_duration": float(r.trip_duration),
        }
        for r in rows
    ]


@router.get("/fare-to-distance-anomalies", response_model=list[FareDistanceAnomalyItem])
def fare_to_distance_anomalies(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Highlight trips with unusually high base fares for very short distances."""
    rows = (
        db.query(
            YellowCab.id,
            YellowCab.trip_distance,
            YellowCab.fare_amount,
        )
        .filter(YellowCab.trip_distance < 0.5)
        .filter(YellowCab.fare_amount > 50)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "trip_distance": float(r.trip_distance),
            "fare_amount": float(r.fare_amount),
        }
        for r in rows
    ]
