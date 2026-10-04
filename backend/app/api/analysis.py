from fastapi import APIRouter, Query

from backend.app.services.analysis_context_service import get_analysis_context


router = APIRouter(prefix="/api/analysis", tags=["Analysis Context"])


@router.get("/context")
def analysis_context(
    city: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    return get_analysis_context(
        city=city,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
    )
