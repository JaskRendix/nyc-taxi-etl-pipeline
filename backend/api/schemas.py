from typing import Any

from pydantic import BaseModel, ConfigDict, RootModel


class Stats(BaseModel):
    rows: int
    avg_fare: float


class TripDistanceStats(BaseModel):
    min: float
    avg: float
    max: float


class TipStats(BaseModel):
    avg_tip: float
    avg_tip_pct: float
    avg_tip_by_hour: list[dict[str, Any]]


class DurationStats(BaseModel):
    min: float
    avg: float
    max: float
    duration_by_hour: list[dict[str, Any]]
    duration_by_distance_bucket: list[dict[str, Any]]


class PaymentTypeBreakdown(RootModel[dict[str, int]]):
    """Root model for mapping payment_type -> count."""

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


class FarePredictionRequest(BaseModel):
    trip_distance: float
    trip_duration: float
    hour: int
    passenger_count: int
    distance_bucket: int
    duration_bucket: int
    speed_mpm: float
    is_peak_hour: int
    is_airport: int


class FarePredictionResponse(BaseModel):
    predicted_fare: float


class RevenueVelocityItem(BaseModel):
    hour: int
    avg_earnings_per_hour: float
    avg_earnings_per_mile: float


class FeeMetric(BaseModel):
    total: float
    average: float


class TollsAndSurchargesResponse(BaseModel):
    tolls: FeeMetric
    improvement_surcharge: FeeMetric
    congestion_surcharge: FeeMetric


class SignalMetric(BaseModel):
    count: int
    percentage: float


class FraudSignalsResponse(BaseModel):
    total_trips: int
    signals: dict[str, SignalMetric]

    # Updated to Pydantic V2 ConfigDict
    model_config = ConfigDict(extra="allow")


class TipOutlierItem(BaseModel):
    id: int
    tip_amount: float
    fare_amount: float
    trip_distance: float
    threshold_used: float


class RouteCircuitousnessItem(BaseModel):
    id: int
    trip_distance: float
    fare_amount: float
    trip_duration: float


class FareDistanceAnomalyItem(BaseModel):
    id: int
    trip_distance: float
    fare_amount: float


class BucketItem(BaseModel):
    bucket: str
    count: int


class OutlierFareItem(BaseModel):
    id: int
    fare: float
    distance: float
    fare_per_mile: float


class DuplicateTripItem(BaseModel):
    pickup: str
    dropoff: str
    pulocation: int
    dolocation: int
    passengers: int
    count: int


class SchemaColumnItem(BaseModel):
    name: str
    type: str


class HourlyDistributionItem(BaseModel):
    hour: int
    count: int


class DayOfWeekTrendItem(BaseModel):
    day_of_week: int
    count: int
    avg_fare: float
    avg_duration: float


class ShiftAnalysisItem(BaseModel):
    shift: str
    count: int
    avg_fare: float
    avg_tip: float
    avg_duration: float


class TaxAndExtraSummaryResponse(BaseModel):
    mta_tax: FeeMetric
    extra: FeeMetric
    airport_fee: FeeMetric
