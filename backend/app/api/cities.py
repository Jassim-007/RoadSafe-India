from fastapi import APIRouter

from backend.app.services.data_service import (
    get_cities_summary,
)


router = APIRouter(
    prefix="/api/cities",
    tags=["Cities"],
)


@router.get("")
def cities():
    return {
        "cities": get_cities_summary()
    }