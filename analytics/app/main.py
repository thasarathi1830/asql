"""PHANTOM Analytics — FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analytics, health, screening

app = FastAPI(
    title="PHANTOM Analytics Engine",
    description="Explainable 8-factor risk scoring, graph analysis, and cryptographic audit API for PHANTOM.",
    version="1.0.0",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Internal-API-Key"],
)

app.include_router(health.router)
app.include_router(analytics.router)
app.include_router(screening.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
