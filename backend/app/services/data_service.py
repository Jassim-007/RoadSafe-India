import pandas as pd

from backend.app.utils.data_loader import (
    load_accidents,
    load_clustered_accidents,
    load_cluster_summary,
    load_cluster_city_summary,
    load_hotspot_candidates,
    load_hotspot_risk,
    load_hotspot_risk_city,
    load_hotspot_factor_city,
)


# ============================================================
# DASHBOARD
# ============================================================

def get_dashboard_summary() -> dict:
    """
    Build the summary information required
    by the RoadSafe India Command Center.
    """

    accidents = load_accidents()
    clustered = load_clustered_accidents()
    hotspots = load_hotspot_risk()

    # --------------------------------------------------------
    # Basic totals
    # --------------------------------------------------------

    total_accidents = len(accidents)

    # DBSCAN cluster IDs
    # -1 represents noise and is NOT a cluster.
    spatial_clusters = clustered.loc[
        clustered["dbscan_cluster"] != -1,
        "dbscan_cluster"
    ].nunique()

    # Number of hotspot candidates
    hotspot_candidates = len(hotspots)

    # --------------------------------------------------------
    # Multiple-indicator hotspots
    # --------------------------------------------------------

    multiple_indicator_hotspots = 0

    if "risk_profile" in hotspots.columns:
        multiple_indicator_hotspots = int(
            (
                hotspots["risk_profile"]
                == "multiple_high_risk_indicators"
            ).sum()
        )

    # --------------------------------------------------------
    # City information
    # --------------------------------------------------------

    city_counts = (
        accidents["city"]
        .value_counts()
        .sort_index()
    )

    cities = []

    for city, count in city_counts.items():
        cities.append(
            {
                "city": city,
                "accidents": int(count),
            }
        )

    # --------------------------------------------------------
    # Clustered records by city
    # --------------------------------------------------------

    clustered_only = clustered[
        (clustered["dbscan_status"] == "clustered")
        & (clustered["dbscan_cluster"] != -1)
    ]

    clustered_city_counts = (
        clustered_only["city"]
        .value_counts()
        .sort_index()
    )

    for city_data in cities:
        city = city_data["city"]

        city_data["clustered_records"] = int(
            clustered_city_counts.get(city, 0)
        )

    # --------------------------------------------------------
    # Dashboard response
    # --------------------------------------------------------

    return {
        "overview": {
            "total_accidents": int(total_accidents),
            "spatial_clusters": int(spatial_clusters),
            "hotspot_candidates": int(hotspot_candidates),
            "multiple_indicator_hotspots": int(
                multiple_indicator_hotspots
            ),
        },

        "cities": cities,

        "dataset": {
            "cities_count": len(cities),
            "start_date": str(
                accidents["date"].min()
            ),
            "end_date": str(
                accidents["date"].max()
            ),
        },
    }


# ============================================================
# CITY INTELLIGENCE
# ============================================================

def get_cities_summary() -> list[dict]:
    """
    Build city-level intelligence for the Cities page.

    Chandigarh remains part of the descriptive city analysis,
    but because it was excluded from DBSCAN, its spatial
    cluster-related values remain zero.
    """

    accidents = load_accidents()
    clustered = load_clustered_accidents()
    hotspots = load_hotspot_risk()

    # --------------------------------------------------------
    # Basic accident statistics
    # --------------------------------------------------------

    city_stats = (
        accidents
        .groupby("city")
        .agg(
            accidents=("accident_id", "count"),

            casualties=("casualties", "sum"),

            fatal_accidents=(
                "accident_severity",
                lambda x: (x == "fatal").sum()
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Fatality proportion
    # --------------------------------------------------------

    city_stats["fatality_proportion"] = (
        city_stats["fatal_accidents"]
        / city_stats["accidents"]
    )

    # --------------------------------------------------------
    # DBSCAN statistics
    # --------------------------------------------------------

    # IMPORTANT:
    # Only actual DBSCAN cluster members are included.
    #
    # dbscan_cluster == -1 means noise.
    #
    # Chandigarh was excluded from DBSCAN and therefore
    # should have zero clustered records and zero clusters.

    clustered_only = clustered[
        (clustered["dbscan_status"] == "clustered")
        & (clustered["dbscan_cluster"] != -1)
    ]

    # Number of spatial clusters by city
    cluster_counts = (
        clustered_only
        .groupby("city")["dbscan_cluster"]
        .nunique()
        .reset_index(
            name="spatial_clusters"
        )
    )

    # Number of records actually inside DBSCAN clusters
    clustered_counts = (
        clustered_only
        .groupby("city")
        .size()
        .reset_index(
            name="clustered_records"
        )
    )

    # --------------------------------------------------------
    # Hotspot statistics
    # --------------------------------------------------------

    hotspot_counts = (
        hotspots
        .groupby("city")
        .size()
        .reset_index(
            name="hotspot_candidates"
        )
    )

    # --------------------------------------------------------
    # Multiple-indicator hotspot statistics
    # --------------------------------------------------------

    if "risk_profile" in hotspots.columns:

        multiple_hotspots = (
            hotspots[
                hotspots["risk_profile"]
                == "multiple_high_risk_indicators"
            ]
            .groupby("city")
            .size()
            .reset_index(
                name="multiple_indicator_hotspots"
            )
        )

    else:

        multiple_hotspots = pd.DataFrame(
            columns=[
                "city",
                "multiple_indicator_hotspots",
            ]
        )

    # --------------------------------------------------------
    # Merge city statistics
    # --------------------------------------------------------

    result = city_stats.merge(
        cluster_counts,
        on="city",
        how="left",
    )

    result = result.merge(
        clustered_counts,
        on="city",
        how="left",
    )

    result = result.merge(
        hotspot_counts,
        on="city",
        how="left",
    )

    result = result.merge(
        multiple_hotspots,
        on="city",
        how="left",
    )

    # --------------------------------------------------------
    # Fill missing DBSCAN / hotspot values
    # --------------------------------------------------------

    numeric_columns = [
        "spatial_clusters",
        "clustered_records",
        "hotspot_candidates",
        "multiple_indicator_hotspots",
    ]

    for column in numeric_columns:

        result[column] = (
            result[column]
            .fillna(0)
            .astype(int)
        )

    # --------------------------------------------------------
    # Format API response
    # --------------------------------------------------------

    cities = []

    for _, row in result.iterrows():

        cities.append(
            {
                "city": row["city"],

                "accidents": int(
                    row["accidents"]
                ),

                "clustered_records": int(
                    row["clustered_records"]
                ),

                "spatial_clusters": int(
                    row["spatial_clusters"]
                ),

                "hotspot_candidates": int(
                    row["hotspot_candidates"]
                ),

                "multiple_indicator_hotspots": int(
                    row["multiple_indicator_hotspots"]
                ),

                "casualties": int(
                    row["casualties"]
                ),

                "fatal_accidents": int(
                    row["fatal_accidents"]
                ),

                "fatality_proportion": round(
                    float(
                        row["fatality_proportion"]
                    ),
                    4,
                ),
            }
        )

    return cities