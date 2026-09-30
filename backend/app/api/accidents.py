from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.services.accident_service import (
    get_accident,
    get_accidents,
)


router = APIRouter(
    prefix="/api/accidents",
    tags=["Accidents"],
)


# ============================================================
# ACCIDENT LIST / MAP DATA
# ============================================================

@router.get("")
def accidents(
    city: Optional[str] = Query(
        default=None,
        description="Filter by city",
    ),

    severity: Optional[str] = Query(
        default=None,
        description="Filter by accident severity",
    ),

    road_type: Optional[str] = Query(
        default=None,
        description="Filter by road type",
    ),

    weather: Optional[str] = Query(
        default=None,
        description="Filter by weather",
    ),

    traffic_density: Optional[str] = Query(
        default=None,
        description="Filter by traffic density",
    ),

    is_peak_hour: Optional[bool] = Query(
        default=None,
        description="Filter by peak-hour status",
    ),

    is_weekend: Optional[bool] = Query(
        default=None,
        description="Filter by weekend status",
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records",
    ),

    offset: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip",
    ),
):

    return get_accidents(
        city=city,
        severity=severity,
        road_type=road_type,
        weather=weather,
        traffic_density=traffic_density,
        is_peak_hour=is_peak_hour,
        is_weekend=is_weekend,
        limit=limit,
        offset=offset,
    )


# ============================================================
# SINGLE ACCIDENT
# ============================================================

@router.get("/{accident_id}")
def accident_detail(
    accident_id: str,
):

    result = get_accident(
        accident_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Accident {accident_id} "
                "not found"
            ),
        )

    return result