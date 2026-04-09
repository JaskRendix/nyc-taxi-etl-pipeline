from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from db import SessionLocal
from models import YellowCab

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(YellowCab).count()
    avg_fare = db.query(YellowCab).with_entities(YellowCab.fare_amount).all()
    avg_fare = sum(f[0] for f in avg_fare) / total if total else 0
    return {"rows": total, "avg_fare": avg_fare}
