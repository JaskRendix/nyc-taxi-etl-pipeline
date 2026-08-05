import pickle
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.schemas import (
    FarePredictionRequest,
    FarePredictionResponse,
    RevenueVelocityItem,
    TaxAndExtraSummaryResponse,
    TollsAndSurchargesResponse,
)
from backend.core.db import get_db
from backend.models import YellowCab

router = APIRouter()


@router.get("/revenue-velocity", response_model=list[RevenueVelocityItem])
def revenue_velocity(db: Session = Depends(get_db)) -> list[RevenueVelocityItem]:
    """Calculate average earnings-per-hour and earnings-per-mile across different hours of the day."""
    rows = (
        db.query(
            YellowCab.hour,
            func.avg(
                YellowCab.total_amount / func.nullif(YellowCab.trip_duration / 3600, 0)
            ).label("earnings_per_hour"),
            func.avg(
                YellowCab.total_amount / func.nullif(YellowCab.trip_distance, 0)
            ).label("earnings_per_mile"),
        )
        .group_by(YellowCab.hour)
        .order_by(YellowCab.hour)
        .all()
    )

    return [
        RevenueVelocityItem(
            hour=h,
            avg_earnings_per_hour=float(eph or 0),
            avg_earnings_per_mile=float(epm or 0),
        )
        for h, eph, epm in rows
    ]


@router.get("/tolls-and-surcharges", response_model=TollsAndSurchargesResponse)
def tolls_and_surcharges(db: Session = Depends(get_db)) -> TollsAndSurchargesResponse:
    """Retrieve a breakdown of extra fees, tolls, and surcharges across all trips."""
    totals = db.query(
        func.sum(YellowCab.tolls_amount).label("total_tolls"),
        func.avg(YellowCab.tolls_amount).label("avg_tolls"),
        func.sum(YellowCab.improvement_surcharge).label("total_improvement_surcharge"),
        func.avg(YellowCab.improvement_surcharge).label("avg_improvement_surcharge"),
        func.sum(YellowCab.congestion_surcharge).label("total_congestion_surcharge"),
        func.avg(YellowCab.congestion_surcharge).label("avg_congestion_surcharge"),
    ).one()

    data = dict(totals._mapping)

    return TollsAndSurchargesResponse(
        tolls={
            "total": float(data.get("total_tolls") or 0),
            "average": float(data.get("avg_tolls") or 0),
        },
        improvement_surcharge={
            "total": float(data.get("total_improvement_surcharge") or 0),
            "average": float(data.get("avg_improvement_surcharge") or 0),
        },
        congestion_surcharge={
            "total": float(data.get("total_congestion_surcharge") or 0),
            "average": float(data.get("avg_congestion_surcharge") or 0),
        },
    )


@router.get("/tax-and-extra-summary", response_model=TaxAndExtraSummaryResponse)
def tax_and_extra_summary(db: Session = Depends(get_db)) -> TaxAndExtraSummaryResponse:
    """Retrieve aggregate summaries of MTA tax, extra charges, and airport fees."""
    totals = db.query(
        func.sum(YellowCab.mta_tax).label("total_mta_tax"),
        func.avg(YellowCab.mta_tax).label("avg_mta_tax"),
        func.sum(YellowCab.extra).label("total_extra"),
        func.avg(YellowCab.extra).label("avg_extra"),
        func.sum(YellowCab.airport_fee).label("total_airport_fee"),
        func.avg(YellowCab.airport_fee).label("avg_airport_fee"),
    ).one()

    data = dict(totals._mapping)

    return TaxAndExtraSummaryResponse(
        mta_tax={
            "total": float(data.get("total_mta_tax") or 0),
            "average": float(data.get("avg_mta_tax") or 0),
        },
        extra={
            "total": float(data.get("total_extra") or 0),
            "average": float(data.get("avg_extra") or 0),
        },
        airport_fee={
            "total": float(data.get("total_airport_fee") or 0),
            "average": float(data.get("avg_airport_fee") or 0),
        },
    )


MODEL_PATH: Path = Path(__file__).resolve().parents[1] / "core" / "fare_model.pkl"


def load_model() -> Any:
    if not MODEL_PATH.exists():
        raise RuntimeError("Model file not found. Train the model first.")
    with MODEL_PATH.open("rb") as f:
        return pickle.load(f)


@router.post("/predict", response_model=FarePredictionResponse)
def predict_fare(payload: FarePredictionRequest) -> FarePredictionResponse:
    """Predict taxi fare using the trained regression model."""
    try:
        model = load_model()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    features: list[Any] = [
        payload.trip_distance,
        payload.trip_duration,
        payload.hour,
        payload.passenger_count,
        payload.distance_bucket,
        payload.duration_bucket,
        payload.speed_mpm,
        payload.is_peak_hour,
        payload.is_airport,
    ]

    try:
        prediction = float(model.predict([features])[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")

    return FarePredictionResponse(predicted_fare=prediction)
