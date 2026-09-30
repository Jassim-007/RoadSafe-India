from fastapi import FastAPI

from backend.app.api.dashboard import (
    router as dashboard_router,
)

from backend.app.api.cities import (
    router as cities_router,
)

from backend.app.api.hotspots import (
    router as hotspots_router,
)

from backend.app.api.accidents import (
    router as accidents_router,
)

from backend.app.api.factors import (
    router as factors_router,
)

from backend.app.api.history import (
    router as history_router,
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="RoadSafe India API",
    description=(
        "Road Accident Intelligence & "
        "Risk Monitoring Platform"
    ),
    version="1.0.0",
)


# ============================================================
# API ROUTERS
# ============================================================

app.include_router(
    dashboard_router
)

app.include_router(
    cities_router
)

app.include_router(
    hotspots_router
)

app.include_router(
    accidents_router
)

app.include_router(
    factors_router
)

app.include_router(
    history_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "RoadSafe India",
        "status": "online",
        "message": (
            "RoadSafe India API is running"
        ),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }