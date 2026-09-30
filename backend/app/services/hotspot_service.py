from typing import Optional

import pandas as pd

from backend.app.utils.data_loader import (
    load_clustered_accidents,
    load_hotspot_risk,
)


# ============================================================
# HOTSPOT SERVICE
# ============================================================

def _prepare_hotspots() -> pd.DataFrame:
    """
    Combine hotspot risk analysis with DBSCAN cluster
    coordinates so the frontend can display hotspots
    on the interactive map.
    """

    hotspots = load_hotspot_risk().copy()
    clustered = load_clustered_accidents().copy()

    # --------------------------------------------------------
    # Keep only actual DBSCAN cluster records
    # --------------------------------------------------------

    clustered = clustered[
        (clustered["dbscan_cluster"] != -1)
        & (clustered["dbscan_status"] == "clustered")
    ].copy()

    # --------------------------------------------------------
    # Calculate geographic centroid for each cluster
    # --------------------------------------------------------

    centroids = (
        clustered
        .groupby(["city", "dbscan_cluster"])
        .agg(
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Merge hotspot analysis with coordinates
    # --------------------------------------------------------

    result = hotspots.merge(
        centroids,
        on=["city", "dbscan_cluster"],
        how="left",
    )

    return result


# ============================================================
# RESPONSE FORMATTER
# ============================================================

def _format_hotspot(row: pd.Series) -> dict:
    """
    Convert one hotspot DataFrame row into
    a clean API response object.
    """

    latitude = row.get("latitude")
    longitude = row.get("longitude")

    return {
        "city": row["city"],
        "cluster_id": int(row["dbscan_cluster"]),

        "location": {
            "latitude": (
                float(latitude)
                if pd.notna(latitude)
                else None
            ),
            "longitude": (
                float(longitude)
                if pd.notna(longitude)
                else None
            ),
        },

        "statistics": {
            "accident_count": int(
                row["accident_count"]
            ),
            "total_casualties": int(
                row["total_casualties"]
            ),
            "mean_casualties": round(
                float(row["mean_casualties"]),
                3,
            ),
            "mean_vehicles": round(
                float(row["mean_vehicles"]),
                3,
            ),
            "mean_risk_score": round(
                float(row["mean_risk_score"]),
                4,
            ),
            "fatal_accidents": int(
                row["fatal_accidents"]
            ),
            "major_accidents": int(
                row["major_accidents"]
            ),
            "minor_accidents": int(
                row["minor_accidents"]
            ),
        },

        "severity": {
            "fatality_proportion": round(
                float(row["fatality_proportion"]),
                4,
            ),
            "major_proportion": round(
                float(row["major_proportion"]),
                4,
            ),
            "severe_proportion": round(
                float(row["severe_proportion"]),
                4,
            ),
        },

        "risk_indicators": {
            "high_accident_density": bool(
                row["high_accident_density"]
            ),
            "high_fatality_proportion": bool(
                row["high_fatality_proportion"]
            ),
            "high_casualty_burden": bool(
                row["high_casualty_burden"]
            ),
            "high_mean_risk_score": bool(
                row["high_mean_risk_score"]
            ),
        },

        "risk_profile": row["risk_profile"],

        "priority_for_mapping": bool(
            row["priority_for_mapping"]
        ),
    }


# ============================================================
# ALL HOTSPOTS
# ============================================================

def get_hotspots(
    city: Optional[str] = None,
    risk_profile: Optional[str] = None,
    priority_only: bool = False,
) -> list[dict]:
    """
    Return hotspot candidates with optional filters.

    Supported filters:
        city
        risk_profile
        priority_only
    """

    hotspots = _prepare_hotspots()

    # --------------------------------------------------------
    # City filter
    # --------------------------------------------------------

    if city:
        hotspots = hotspots[
            hotspots["city"].str.lower()
            == city.lower()
        ]

    # --------------------------------------------------------
    # Risk profile filter
    # --------------------------------------------------------

    if risk_profile:
        hotspots = hotspots[
            hotspots["risk_profile"].str.lower()
            == risk_profile.lower()
        ]

    # --------------------------------------------------------
    # Priority filter
    # --------------------------------------------------------

    if priority_only:
        hotspots = hotspots[
            hotspots["priority_for_mapping"] == True
        ]

    # --------------------------------------------------------
    # Sort by accident count
    # --------------------------------------------------------

    hotspots = hotspots.sort_values(
        by=[
            "accident_count",
            "total_casualties",
        ],
        ascending=False,
    )

    return [
        _format_hotspot(row)
        for _, row in hotspots.iterrows()
    ]


# ============================================================
# SINGLE HOTSPOT
# ============================================================

def get_hotspot(
    city: str,
    cluster_id: int,
) -> Optional[dict]:
    """
    Return a single hotspot by city and DBSCAN cluster ID.
    """

    hotspots = _prepare_hotspots()

    result = hotspots[
        (hotspots["city"].str.lower() == city.lower())
        & (
            hotspots["dbscan_cluster"]
            == cluster_id
        )
    ]

    if result.empty:
        return None

    return _format_hotspot(
        result.iloc[0]
    )


# ============================================================
# CITY HOTSPOTS
# ============================================================

def get_city_hotspots(
    city: str,
) -> list[dict]:
    """
    Return all hotspot candidates belonging
    to a specific city.
    """

    return get_hotspots(
        city=city
    )