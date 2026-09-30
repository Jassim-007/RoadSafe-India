from fastapi import APIRouter

from backend.app.services.data_service import (
    get_dashboard_summary,
)


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("")
def dashboard():
    return get_dashboard_summary()