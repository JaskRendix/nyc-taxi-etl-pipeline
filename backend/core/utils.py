from sqlalchemy import func
from sqlalchemy.orm import Session


def bucket_query(db: Session, column, start: float, end: float, buckets: int):
    return (
        db.query(
            func.width_bucket(column, start, end, buckets).label("bucket"),
            func.count(),
        )
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )
