from fastapi import APIRouter

from backend.app.services.history_service import (
    get_kerala_history,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/history",
    tags=["History"],
)


# ============================================================
# KERALA HISTORY
# ============================================================

@router.get("/kerala")
def kerala_history():
    """
    Return historical Kerala black-spot data.
    """

    return get_kerala_history()