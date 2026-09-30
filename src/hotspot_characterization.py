from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "clusters"
    / "final_clustered_accidents.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "clusters"
)

CLUSTER_SUMMARY_FILE = (
    OUTPUT_DIR
    / "hotspot_characterization.csv"
)

HOTSPOT_CANDIDATES_FILE = (
    OUTPUT_DIR
    / "hotspot_candidates.csv"
)


# ============================================================
# SETTINGS
# ============================================================

# Minimum number of accidents for a cluster to be included
# in the hotspot candidate analysis.
#
# This does NOT mean a cluster below this size is unsafe.
# It is simply a practical minimum for characterization.

MIN_ACCIDENTS = 15


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 75)
print("HOTSPOT CHARACTERIZATION")
print("=" * 75)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Could not find:\n{INPUT_FILE}\n\n"
        "Run final_dbscan.py first."
    )


df = pd.read_csv(
    INPUT_FILE
)


print(
    f"\nRecords loaded: "
    f"{len(df):,}"
)


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = {
    "accident_id",
    "city",
    "latitude",
    "longitude",
    "dbscan_cluster",
    "dbscan_status",
    "accident_severity",
    "casualties",
    "risk_score",
    "cause",
    "road_type",
    "weather",
    "traffic_density",
    "vehicles_involved",
}

missing = (
    required_columns
    - set(df.columns)
)

if missing:
    raise ValueError(
        f"Missing required columns: "
        f"{sorted(missing)}"
    )


# ============================================================
# KEEP ONLY ACTUAL DBSCAN CLUSTERS
# ============================================================

clustered = df[
    (df["dbscan_status"] == "clustered")
    & (df["dbscan_cluster"] != -1)
].copy()


print(
    f"Records inside DBSCAN clusters: "
    f"{len(clustered):,}"
)


print(
    f"Spatial clusters: "
    f"{clustered['dbscan_cluster'].nunique():,}"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def mode_value(series):
    """
    Return the most frequent non-null value.
    """
    series = series.dropna()

    if series.empty:
        return np.nan

    return series.mode().iloc[0]


def percentage(part, total):
    """
    Safe percentage calculation.
    """
    if total == 0:
        return 0.0

    return (
        part
        / total
        * 100
    )


# ============================================================
# BUILD CLUSTER CHARACTERISTICS
# ============================================================

cluster_rows = []


for (cluster_id, city), group in (
    clustered.groupby(
        [
            "dbscan_cluster",
            "city",
        ],
        sort=True
    )
):

    accident_count = len(group)


    # --------------------------------------------------------
    # SEVERITY
    # --------------------------------------------------------

    fatal_count = int(
        (
            group["accident_severity"]
            .str.lower()
            == "fatal"
        ).sum()
    )

    major_count = int(
        (
            group["accident_severity"]
            .str.lower()
            == "major"
        ).sum()
    )

    minor_count = int(
        (
            group["accident_severity"]
            .str.lower()
            == "minor"
        ).sum()
    )


    # --------------------------------------------------------
    # CASUALTIES
    # --------------------------------------------------------

    total_casualties = (
        group["casualties"]
        .sum()
    )

    mean_casualties = (
        group["casualties"]
        .mean()
    )

    median_casualties = (
        group["casualties"]
        .median()
    )


    # --------------------------------------------------------
    # RISK SCORE
    # --------------------------------------------------------

    mean_risk_score = (
        group["risk_score"]
        .mean()
    )

    median_risk_score = (
        group["risk_score"]
        .median()
    )

    max_risk_score = (
        group["risk_score"]
        .max()
    )


    # --------------------------------------------------------
    # VEHICLES
    # --------------------------------------------------------

    mean_vehicles = (
        group["vehicles_involved"]
        .mean()
    )


    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    centroid_latitude = (
        group["latitude"]
        .mean()
    )

    centroid_longitude = (
        group["longitude"]
        .mean()
    )


    # --------------------------------------------------------
    # DOMINANT CHARACTERISTICS
    # --------------------------------------------------------

    dominant_cause = mode_value(
        group["cause"]
    )

    dominant_road_type = mode_value(
        group["road_type"]
    )

    dominant_weather = mode_value(
        group["weather"]
    )

    dominant_traffic_density = mode_value(
        group["traffic_density"]
    )


    # --------------------------------------------------------
    # PEAK / WEEKEND CHARACTERISTICS
    # --------------------------------------------------------

    if "is_peak_hour" in group.columns:

        peak_hour_percentage = (
            group["is_peak_hour"]
            .mean()
            * 100
        )

    else:

        peak_hour_percentage = np.nan


    if "is_weekend" in group.columns:

        weekend_percentage = (
            group["is_weekend"]
            .mean()
            * 100
        )

    else:

        weekend_percentage = np.nan


    # --------------------------------------------------------
    # ADD ROW
    # --------------------------------------------------------

    cluster_rows.append({

        "cluster_id":
            int(cluster_id),

        "city":
            city,

        "accident_count":
            accident_count,

        "fatal_accidents":
            fatal_count,

        "major_accidents":
            major_count,

        "minor_accidents":
            minor_count,

        "fatal_percentage":
            percentage(
                fatal_count,
                accident_count
            ),

        "major_percentage":
            percentage(
                major_count,
                accident_count
            ),

        "minor_percentage":
            percentage(
                minor_count,
                accident_count
            ),

        "total_casualties":
            total_casualties,

        "mean_casualties":
            mean_casualties,

        "median_casualties":
            median_casualties,

        "mean_risk_score":
            mean_risk_score,

        "median_risk_score":
            median_risk_score,

        "max_risk_score":
            max_risk_score,

        "mean_vehicles_involved":
            mean_vehicles,

        "centroid_latitude":
            centroid_latitude,

        "centroid_longitude":
            centroid_longitude,

        "dominant_cause":
            dominant_cause,

        "dominant_road_type":
            dominant_road_type,

        "dominant_weather":
            dominant_weather,

        "dominant_traffic_density":
            dominant_traffic_density,

        "peak_hour_percentage":
            peak_hour_percentage,

        "weekend_percentage":
            weekend_percentage,
    })


# ============================================================
# CREATE DATAFRAME
# ============================================================

cluster_summary = pd.DataFrame(
    cluster_rows
)


# ============================================================
# SORT
# ============================================================

cluster_summary = cluster_summary.sort_values(
    [
        "city",
        "accident_count",
    ],
    ascending=[
        True,
        False,
    ]
).reset_index(
    drop=True
)


# ============================================================
# CITY-WISE ACCIDENT DENSITY RANK
# ============================================================

# Rank clusters by accident count within each city.
#
# This is a descriptive rank only. It does NOT mean that
# the highest-count cluster is automatically the most dangerous.

cluster_summary[
    "city_accident_count_rank"
] = (
    cluster_summary
    .groupby("city")[
        "accident_count"
    ]
    .rank(
        ascending=False,
        method="dense"
    )
    .astype(int)
)


# ============================================================
# HOTSPOT CANDIDATE FLAG
# ============================================================

cluster_summary[
    "hotspot_candidate"
] = (
    cluster_summary["accident_count"]
    >= MIN_ACCIDENTS
)


# ============================================================
# SAVE COMPLETE CHARACTERIZATION
# ============================================================

cluster_summary.to_csv(
    CLUSTER_SUMMARY_FILE,
    index=False
)


# ============================================================
# SAVE HOTSPOT CANDIDATES
# ============================================================

hotspot_candidates = cluster_summary[
    cluster_summary["hotspot_candidate"]
].copy()


hotspot_candidates.to_csv(
    HOTSPOT_CANDIDATES_FILE,
    index=False
)


# ============================================================
# PRINT OVERVIEW
# ============================================================

print("\n" + "=" * 75)
print("CLUSTER CHARACTERIZATION SUMMARY")
print("=" * 75)

print(
    f"\nTotal DBSCAN clusters: "
    f"{len(cluster_summary):,}"
)

print(
    f"Clusters with at least "
    f"{MIN_ACCIDENTS} accidents: "
    f"{len(hotspot_candidates):,}"
)


# ============================================================
# CITY-WISE SUMMARY
# ============================================================

print("\n" + "=" * 75)
print("CITY-WISE HOTSPOT CANDIDATES")
print("=" * 75)


city_summary = (
    cluster_summary
    .groupby("city")
    .agg(
        total_clusters=(
            "cluster_id",
            "count"
        ),
        hotspot_candidates=(
            "hotspot_candidate",
            "sum"
        ),
        total_clustered_accidents=(
            "accident_count",
            "sum"
        ),
        largest_cluster=(
            "accident_count",
            "max"
        ),
        mean_cluster_size=(
            "accident_count",
            "mean"
        ),
        mean_risk_score=(
            "mean_risk_score",
            "mean"
        ),
        total_casualties=(
            "total_casualties",
            "sum"
        ),
    )
    .reset_index()
)


print(
    city_summary.to_string(
        index=False
    )
)


# ============================================================
# TOP CLUSTERS BY ACCIDENT COUNT
# ============================================================

print("\n" + "=" * 75)
print("TOP SPATIAL CLUSTERS BY ACCIDENT COUNT")
print("=" * 75)

top_clusters = cluster_summary[
    [
        "cluster_id",
        "city",
        "accident_count",
        "fatal_percentage",
        "total_casualties",
        "mean_risk_score",
        "dominant_cause",
        "dominant_road_type",
        "centroid_latitude",
        "centroid_longitude",
    ]
].sort_values(
    "accident_count",
    ascending=False
).head(20)


print(
    top_clusters.to_string(
        index=False
    )
)


# ============================================================
# TOP CLUSTERS BY FATAL PERCENTAGE
# ============================================================

print("\n" + "=" * 75)
print("TOP CLUSTERS BY FATAL-ACCIDENT PERCENTAGE")
print("=" * 75)

fatal_candidates = cluster_summary[
    cluster_summary["accident_count"]
    >= MIN_ACCIDENTS
].sort_values(
    "fatal_percentage",
    ascending=False
).head(20)


print(
    fatal_candidates[
        [
            "cluster_id",
            "city",
            "accident_count",
            "fatal_accidents",
            "fatal_percentage",
            "total_casualties",
            "mean_risk_score",
            "centroid_latitude",
            "centroid_longitude",
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# TOP CLUSTERS BY CASUALTIES
# ============================================================

print("\n" + "=" * 75)
print("TOP CLUSTERS BY TOTAL CASUALTIES")
print("=" * 75)

casualty_candidates = cluster_summary[
    cluster_summary["accident_count"]
    >= MIN_ACCIDENTS
].sort_values(
    "total_casualties",
    ascending=False
).head(20)


print(
    casualty_candidates[
        [
            "cluster_id",
            "city",
            "accident_count",
            "total_casualties",
            "mean_casualties",
            "fatal_accidents",
            "fatal_percentage",
            "mean_risk_score",
            "centroid_latitude",
            "centroid_longitude",
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# OUTPUT FILES
# ============================================================

print("\n" + "=" * 75)
print("FILES SAVED")
print("=" * 75)

print(
    f"\nComplete characterization:"
    f"\n{CLUSTER_SUMMARY_FILE}"
)

print(
    f"\nHotspot candidates:"
    f"\n{HOTSPOT_CANDIDATES_FILE}"
)


print("\nHotspot characterization complete.")