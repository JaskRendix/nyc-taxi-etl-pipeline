from pydantic import BaseModel, RootModel


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
    avg_tip_by_hour: list[dict]


class DurationStats(BaseModel):
    min: float
    avg: float
    max: float
    duration_by_hour: list[dict]
    duration_by_distance_bucket: list[dict]


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
