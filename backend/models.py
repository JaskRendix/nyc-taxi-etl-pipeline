from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class YellowCab(Base):
    __tablename__ = "yellowcab_cleaned"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Core trip metadata
    VendorID: Mapped[int | None] = mapped_column(Integer)
    tpep_pickup_datetime: Mapped[datetime | None] = mapped_column(DateTime)
    tpep_dropoff_datetime: Mapped[datetime | None] = mapped_column(DateTime)
    passenger_count: Mapped[int | None] = mapped_column(Integer)

    # Distance, duration, fare
    trip_distance: Mapped[float | None] = mapped_column(Float)
    trip_duration: Mapped[float | None] = mapped_column(Float)
    fare_amount: Mapped[float | None] = mapped_column(Float)
    tip_amount: Mapped[float | None] = mapped_column(Float)

    # Location IDs
    PULocationID: Mapped[int | None] = mapped_column(Integer)
    DOLocationID: Mapped[int | None] = mapped_column(Integer)

    # Payment & surcharges
    payment_type: Mapped[int | None] = mapped_column(Integer)
    extra: Mapped[float | None] = mapped_column(Float)
    mta_tax: Mapped[float | None] = mapped_column(Float)
    tolls_amount: Mapped[float | None] = mapped_column(Float)
    improvement_surcharge: Mapped[float | None] = mapped_column(Float)
    congestion_surcharge: Mapped[float | None] = mapped_column(Float)
    airport_fee: Mapped[float | None] = mapped_column(Float)
    total_amount: Mapped[float | None] = mapped_column(Float)

    # Derived analytics fields
    hour: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(String(50))
    is_short_expensive: Mapped[int | None] = mapped_column(Integer)
    is_long_duration: Mapped[int | None] = mapped_column(Integer)
    is_cheap_per_mile: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        # Single-column analytical indexes
        Index("idx_yellowcab_pickup", "tpep_pickup_datetime"),
        Index("idx_yellowcab_fare", "fare_amount"),
        Index("idx_yellowcab_distance", "trip_distance"),
        Index("idx_yellowcab_tip", "tip_amount"),
        Index("idx_yellowcab_payment", "payment_type"),
        Index("idx_yellowcab_hour", "hour"),
        # Corridor analytics (Composite)
        Index("idx_yellowcab_pu_do", "PULocationID", "DOLocationID"),
        Index("idx_yellowcab_hour_pu_do", "hour", "PULocationID", "DOLocationID"),
        # Fraud & anomaly detection (Composite)
        Index("idx_yellowcab_duration_distance", "trip_duration", "trip_distance"),
        Index("idx_yellowcab_flags", "is_short_expensive", "is_cheap_per_mile"),
    )
