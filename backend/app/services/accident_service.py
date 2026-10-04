from typing import Optional

import pandas as pd

from backend.app.utils.data_loader import load_accidents


# ============================================================
# ACCIDENT SERVICE
# ============================================================

def _prepare_accidents() -> pd.DataFrame:
    """
    Load the cleaned accident dataset.
    """

    return load_accidents().copy()


# ============================================================
# FORMAT ONE ACCIDENT
# ============================================================

def _format_accident(row: pd.Series) -> dict:
    """
    Convert one accident record into a clean,
    frontend-friendly API response.

    Important:
    - latitude / longitude are numeric
    - visibility is categorical
    - weather is categorical
    - traffic density is categorical
    """

    return {
        "accident_id": str(
            row["accident_id"]
        ),

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        "location": {
            "latitude": float(
                row["latitude"]
            ),
            "longitude": float(
                row["longitude"]
            ),
        },

        # ----------------------------------------------------
        # ADMINISTRATIVE LOCATION
        # ----------------------------------------------------

        "city": str(
            row["city"]
        ),

        "state": str(
            row["state"]
        ),

        # ----------------------------------------------------
        # DATE / TIME
        # ----------------------------------------------------

        "date": str(
            row["date"]
        ),

        "time": str(
            row["time"]
        ),

        "hour": int(
            row["hour"]
        ),

        "day_of_week": str(
            row["day_of_week"]
        ),

        "is_weekend": bool(
            row["is_weekend"]
        ),

        "is_peak_hour": bool(
            row["is_peak_hour"]
        ),

        # ----------------------------------------------------
        # ROAD
        # ----------------------------------------------------

        "road_type": str(
            row["road_type"]
        ),

        "lanes": int(
            row["lanes"]
        ),

        "traffic_signal": int(
            row["traffic_signal"]
        ),

        # ----------------------------------------------------
        # ENVIRONMENT
        # ----------------------------------------------------

        "weather": str(
            row["weather"]
        ),

        "visibility": str(
            row["visibility"]
        ),

        "temperature": float(
            row["temperature"]
        ),

        # ----------------------------------------------------
        # TRAFFIC / CAUSE
        # ----------------------------------------------------

        "traffic_density": str(
            row["traffic_density"]
        ),

        "cause": str(
            row["cause"]
        ),

        # ----------------------------------------------------
        # SEVERITY
        # ----------------------------------------------------

        "severity": str(
            row["accident_severity"]
        ),

        # ----------------------------------------------------
        # IMPACT
        # ----------------------------------------------------

        "vehicles_involved": int(
            row["vehicles_involved"]
        ),

        "casualties": int(
            row["casualties"]
        ),

        # ----------------------------------------------------
        # EXISTING RISK SCORE
        # ----------------------------------------------------

        "risk_score": float(
            row["risk_score"]
        ),
    }


# ============================================================
# ACCIDENT LIST
# ============================================================

def get_accidents(
    city: Optional[str] = None,
    severity: Optional[str] = None,
    road_type: Optional[str] = None,
    weather: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    traffic_density: Optional[str] = None,
    is_peak_hour: Optional[bool] = None,
    is_weekend: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:

    accidents = _prepare_accidents()

    # --------------------------------------------------------
    # CITY
    # --------------------------------------------------------

    if city:
        accidents = accidents[
            accidents["city"]
            .astype(str)
            .str.lower()
            == city.lower()
        ]

    # --------------------------------------------------------
    # SEVERITY
    # --------------------------------------------------------

    if severity:
        accidents = accidents[
            accidents["accident_severity"]
            .astype(str)
            .str.lower()
            == severity.lower()
        ]

    if start_date:
        accidents = accidents[accidents["date"] >= start_date]

    if end_date:
        accidents = accidents[accidents["date"] <= end_date]

    # --------------------------------------------------------
    # ROAD TYPE
    # --------------------------------------------------------

    if road_type:
        accidents = accidents[
            accidents["road_type"]
            .astype(str)
            .str.lower()
            == road_type.lower()
        ]

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    if weather:
        accidents = accidents[
            accidents["weather"]
            .astype(str)
            .str.lower()
            == weather.lower()
        ]

    # --------------------------------------------------------
    # TRAFFIC DENSITY
    # --------------------------------------------------------

    if traffic_density:
        accidents = accidents[
            accidents["traffic_density"]
            .astype(str)
            .str.lower()
            == traffic_density.lower()
        ]

    # --------------------------------------------------------
    # PEAK HOUR
    # --------------------------------------------------------

    if is_peak_hour is not None:
        accidents = accidents[
            accidents["is_peak_hour"]
            == int(is_peak_hour)
        ]

    # --------------------------------------------------------
    # WEEKEND
    # --------------------------------------------------------

    if is_weekend is not None:
        accidents = accidents[
            accidents["is_weekend"]
            == int(is_weekend)
        ]

    # --------------------------------------------------------
    # TOTAL AFTER FILTERS
    # --------------------------------------------------------

    total = len(accidents)

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    paginated = accidents.iloc[
        offset:offset + limit
    ]

    results = [
        _format_accident(row)
        for _, row in paginated.iterrows()
    ]

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "total": int(total),
        "limit": int(limit),
        "offset": int(offset),
        "count": len(results),
        "accidents": results,
    }


# ============================================================
# SINGLE ACCIDENT
# ============================================================

def get_accident(
    accident_id: str,
) -> Optional[dict]:
    """
    Return one accident by accident_id.
    """

    accidents = _prepare_accidents()

    result = accidents[
        accidents["accident_id"]
        .astype(str)
        == str(accident_id)
    ]

    if result.empty:
        return None

    return _format_accident(
        result.iloc[0]
    )
