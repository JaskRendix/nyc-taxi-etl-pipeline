from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.models import Base, YellowCab


@pytest.fixture(scope="session")
def pg_engine():
    # Connect to the default "postgres" database
    admin_engine = create_engine(
        "postgresql://postgres:postgres@localhost:5432/postgres",
        isolation_level="AUTOCOMMIT",
    )

    # Create test database if missing
    with admin_engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname='test_yellowcab';")
        )
        exists = result.scalar() is not None

        if not exists:
            conn.execute(text("CREATE DATABASE test_yellowcab;"))

    # Now connect to the test DB
    engine = create_engine(
        "postgresql://postgres:postgres@localhost:5432/test_yellowcab"
    )

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    return engine


@pytest.fixture
def db(pg_engine):
    SessionLocal = sessionmaker(bind=pg_engine)
    session = SessionLocal()

    # Clean the table before each test
    session.execute(text("TRUNCATE yellowcab_cleaned RESTART IDENTITY CASCADE"))

    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_crud_roundtrip(db):
    trip = YellowCab(
        VendorID=1,
        tpep_pickup_datetime=datetime(2026, 6, 1, 10, tzinfo=UTC),
        tpep_dropoff_datetime=datetime(2026, 6, 1, 10, 15, tzinfo=UTC),
        passenger_count=1,
        trip_distance=2.5,
        fare_amount=12.50,
        tip_amount=2.00,
        PULocationID=161,
        DOLocationID=236,
        payment_type=1,
        total_amount=15.00,
        hour=10,
        reason="Normal trip",
        is_short_expensive=0,
        is_long_duration=0,
        is_cheap_per_mile=0,
    )

    db.add(trip)
    db.commit()

    saved = db.query(YellowCab).filter_by(VendorID=1).first()

    assert saved is not None
    assert saved.trip_distance == 2.5
    assert saved.fare_amount == 12.50
    assert saved.PULocationID == 161
    assert saved.DOLocationID == 236


@pytest.mark.parametrize(
    "distance,fare,pax",
    [
        (0.0, 10.0, 1),  # zero distance
        (1.0, -5.0, 2),  # negative fare
        (3.2, 12.0, None),  # null passenger count
        (50.0, 100.0, 0),  # zero passengers
    ],
)
def test_edge_cases(db, distance, fare, pax):
    trip = YellowCab(
        trip_distance=distance,
        fare_amount=fare,
        passenger_count=pax,
        tpep_pickup_datetime=datetime.now(UTC),
        tpep_dropoff_datetime=datetime.now(UTC),
    )
    db.add(trip)
    db.commit()

    saved = db.query(YellowCab).first()
    assert saved.trip_distance == distance
    assert saved.fare_amount == fare
    assert saved.passenger_count == pax


def test_index_definitions():
    index_names = {idx.name for idx in YellowCab.__table__.indexes}

    expected = {
        "idx_yellowcab_pickup",
        "idx_yellowcab_fare",
        "idx_yellowcab_distance",
        "idx_yellowcab_tip",
        "idx_yellowcab_payment",
        "idx_yellowcab_hour",
        "idx_yellowcab_pu_do",
        "idx_yellowcab_hour_pu_do",
        "idx_yellowcab_duration_distance",
        "idx_yellowcab_flags",
    }

    assert expected.issubset(index_names)


def test_filter_by_hour(db):
    trip = YellowCab(hour=5)
    db.add(trip)
    db.commit()

    result = db.query(YellowCab).filter(YellowCab.hour == 5).all()
    assert len(result) == 1


def test_filter_by_location_pair(db):
    trip = YellowCab(PULocationID=10, DOLocationID=20)
    db.add(trip)
    db.commit()

    result = (
        db.query(YellowCab)
        .filter(YellowCab.PULocationID == 10, YellowCab.DOLocationID == 20)
        .all()
    )
    assert len(result) == 1


def test_explain_uses_pu_do_index(pg_engine):
    with pg_engine.connect() as conn:
        plan = conn.execute(
            text(
                """
            EXPLAIN ANALYZE
            SELECT *
            FROM yellowcab_cleaned
            WHERE "PULocationID" = 10 AND "DOLocationID" = 20;
        """
            )
        ).fetchall()

        plan_text = "\n".join(row[0] for row in plan)
        assert "idx_yellowcab_pu_do" in plan_text


def test_null_fields(db):
    trip = YellowCab(
        VendorID=None,
        passenger_count=None,
        trip_distance=None,
        fare_amount=None,
        hour=None,
    )
    db.add(trip)
    db.commit()

    saved = db.query(YellowCab).first()
    assert saved.VendorID is None
    assert saved.passenger_count is None
    assert saved.trip_distance is None


@pytest.mark.parametrize(
    "distance,duration,fare,tip",
    [
        (1.2, 300, 8.0, 2.0),  # short cheap
        (12.0, 1800, 45.0, 10.0),  # long expensive
        (0.0, 0, 0.0, 0.0),  # zero trip
        (25.0, 900, 15.0, 0.0),  # long distance low fare
    ],
)
def test_realistic_scenarios(db, distance, duration, fare, tip):
    trip = YellowCab(
        trip_distance=distance,
        trip_duration=duration,
        fare_amount=fare,
        tip_amount=tip,
        tpep_pickup_datetime=datetime.now(UTC),
        tpep_dropoff_datetime=datetime.now(UTC),
    )
    db.add(trip)
    db.commit()

    saved = db.query(YellowCab).first()
    assert saved.trip_distance == distance
    assert saved.fare_amount == fare
