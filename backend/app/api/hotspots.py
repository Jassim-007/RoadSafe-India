from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.services.hotspot_service import (
    get_city_hotspots,
    get_hotspot,
    get_hotspots,
)


router = APIRouter(
    prefix="/api/hotspots",
    tags=["Hotspots"],
)


# ============================================================
# ALL HOTSPOTS
# ============================================================

@router.get("")
def hotspots(
    city: Optional[str] = Query(
        default=None,
        description="Filter hotspots by city",
    ),

    risk_profile: Optional[str] = Query(
        default=None,
        description="Filter by risk profile",
    ),

    priority_only: bool = Query(
        default=False,
        description="Return only priority hotspots",
    ),
):
    """
    Return hotspot candidates with optional filters.
    """

    results = get_hotspots(
        city=city,
        risk_profile=risk_profile,
        priority_only=priority_only,
    )

    return {
        "count": len(results),
        "hotspots": results,
    }


# ============================================================
# CITY HOTSPOTS
# ============================================================

@router.get("/{city}")
def city_hotspots(
    city: str,
):
    """
    Return all hotspot candidates for a city.
    """

    results = get_city_hotspots(city)

    return {
        "city": city,
        "count": len(results),
        "hotspots": results,
    }


# ============================================================
# SINGLE HOTSPOT
# ============================================================

@router.get("/{city}/{cluster_id}")
def hotspot_detail(
    city: str,
    cluster_id: int,
):
    """
    Return detailed information about a specific hotspot.
    """

    result = get_hotspot(
        city=city,
        cluster_id=cluster_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Hotspot {cluster_id} "
                f"not found in {city}"
            ),
        )

    return result