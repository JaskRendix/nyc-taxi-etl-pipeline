from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.models import YellowCab

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        count = db.query(func.count(YellowCab.id)).scalar()
        return {"status": "ok", "db": "connected", "rows": count}
    except Exception:
        return {"status": "error", "db": "unreachable", "rows": None}
