from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class YellowCab(Base):
    __tablename__ = "yellowcab_cleaned"

    VendorID = Column(Integer)
    tpep_pickup_datetime = Column(DateTime)
    tpep_dropoff_datetime = Column(DateTime)
    passenger_count = Column(Integer)
    trip_distance = Column(Float)
    RatecodeID = Column(Integer)
    store_and_fwd_flag = Column(String)
    PULocationID = Column(Integer)
    DOLocationID = Column(Integer)
    payment_type = Column(Integer)
    fare_amount = Column(Float)
    extra = Column(Float)
    mta_tax = Column(Float)
    tip_amount = Column(Float)
    tolls_amount = Column(Float)
    improvement_surcharge = Column(Float)
    total_amount = Column(Float)
    congestion_surcharge = Column(Float)
    airport_fee = Column(Float)
    trip_duration = Column(Float)
    hour = Column(Integer)
    reason = Column(String)
    is_short_expensive = Column(Integer)
    is_long_duration = Column(Integer)
    is_cheap_per_mile = Column(Integer)

    # Add a primary key (required by SQLAlchemy)
    id = Column(Integer, primary_key=True, autoincrement=True)
