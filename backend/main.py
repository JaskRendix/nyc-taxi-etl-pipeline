from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import buckets, financial, fraud, health, locations, samples, stats

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats.router, prefix="/api")
app.include_router(buckets.router, prefix="/api")
app.include_router(fraud.router, prefix="/api")
app.include_router(locations.router, prefix="/api")
app.include_router(samples.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(financial.router, prefix="/api")
