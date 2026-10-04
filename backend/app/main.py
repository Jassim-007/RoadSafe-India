from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.cities import router as cities_router
from backend.app.api.hotspots import router as hotspots_router
from backend.app.api.accidents import router as accidents_router
from backend.app.api.factors import router as factors_router
from backend.app.api.history import router as history_router
from backend.app.api.analysis import router as analysis_router


app = FastAPI(
    title="RoadSafe India API",
    description="Road Accident Intelligence & Risk Monitoring Platform",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------

app.include_router(dashboard_router)
app.include_router(cities_router)
app.include_router(hotspots_router)
app.include_router(accidents_router)
app.include_router(factors_router)
app.include_router(history_router)
app.include_router(analysis_router)


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "name": "RoadSafe India",
        "status": "online",
        "message": "RoadSafe India API is running",
    }


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
    }
