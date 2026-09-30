from fastapi import APIRouter, HTTPException

from backend.app.services.factor_service import (
    get_factor_summary,
    get_factor,
    get_numeric_factor_summary,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/factors",
    tags=["Risk Factors"],
)


# ============================================================
# ALL FACTORS
# ============================================================

@router.get("")
def factors():
    """
    Return all available risk-factor analyses.
    """

    return {
        "factors": get_factor_summary()
    }


# ============================================================
# NUMERIC FACTORS
# ============================================================

@router.get("/numeric")
def numeric_factors():
    """
    Return numeric statistics for clustered accidents.
    """

    return get_numeric_factor_summary()


# ============================================================
# SINGLE FACTOR
# ============================================================

@router.get("/{factor_name}")
def factor(factor_name: str):
    """
    Return one specific risk factor.
    """

    result = get_factor(factor_name)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown factor: {factor_name}",
        )

    return result