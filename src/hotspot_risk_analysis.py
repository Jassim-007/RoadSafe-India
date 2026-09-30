"""
RoadSafe India
Hotspot Risk Analysis

Purpose:
    Characterize DBSCAN spatial clusters using:
    - Accident count
    - Fatality proportion
    - Major/fatal accident proportion
    - Total casualties
    - Mean casualties
    - Vehicles involved
    - Existing risk_score

Important:
    DBSCAN identifies spatially dense accident clusters.
    A DBSCAN cluster is NOT automatically a high-risk hotspot.

    This script uses city-relative percentiles to identify clusters
    that show elevated values across different risk indicators.

    No artificial composite risk score is created.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

CLUSTER_FILE = (
    BASE_DIR
    / "outputs"
    / "clusters"
    / "final_clustered_accidents.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "clusters"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SETTINGS
# ============================================================

# Minimum number of accidents required for a cluster
# to be considered a hotspot candidate.
MIN_ACCIDENTS = 15


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("ROADSAFE INDIA - HOTSPOT RISK ANALYSIS")
print("=" * 70)

print("\nLoading clustered accident data...")

df = pd.read_csv(CLUSTER_FILE)

print(f"Records loaded: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "city",
    "dbscan_cluster",
    "dbscan_status",
    "accident_severity",
    "casualties",
    "vehicles_involved",
    "risk_score",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ============================================================
# CHECK DBSCAN STATUS
# ============================================================

print("\nDBSCAN status distribution:")

print(
    df["dbscan_status"]
    .value_counts(dropna=False)
    .to_string()
)


# ============================================================
# REMOVE DBSCAN NOISE
# ============================================================

# DBSCAN noise is represented by dbscan_cluster == -1.
#
# We only characterize actual spatial clusters here.
# Noise is retained in the original dataset.

clustered = df[
    df["dbscan_cluster"] != -1
].copy()

noise = df[
    df["dbscan_cluster"] == -1
].copy()

print(
    f"\nRecords inside DBSCAN clusters: "
    f"{len(clustered):,}"
)

print(
    f"Noise records excluded: "
    f"{len(noise):,}"
)


# ============================================================
# CLUSTER-LEVEL AGGREGATION
# ============================================================

print("\nCalculating cluster-level statistics...")

cluster_stats = (
    clustered
    .groupby(
        ["city", "dbscan_cluster"],
        as_index=False
    )
    .agg(
        accident_count=(
            "dbscan_cluster",
            "size"
        ),

        total_casualties=(
            "casualties",
            "sum"
        ),

        mean_casualties=(
            "casualties",
            "mean"
        ),

        mean_vehicles=(
            "vehicles_involved",
            "mean"
        ),

        mean_risk_score=(
            "risk_score",
            "mean"
        ),

        fatal_accidents=(
            "accident_severity",
            lambda x: (
                x == "fatal"
            ).sum()
        ),

        major_accidents=(
            "accident_severity",
            lambda x: (
                x == "major"
            ).sum()
        ),

        minor_accidents=(
            "accident_severity",
            lambda x: (
                x == "minor"
            ).sum()
        ),
    )
)


# ============================================================
# DERIVED METRICS
# ============================================================

cluster_stats["fatality_proportion"] = (
    cluster_stats["fatal_accidents"]
    / cluster_stats["accident_count"]
)

cluster_stats["major_proportion"] = (
    cluster_stats["major_accidents"]
    / cluster_stats["accident_count"]
)

cluster_stats["severe_proportion"] = (
    (
        cluster_stats["fatal_accidents"]
        + cluster_stats["major_accidents"]
    )
    / cluster_stats["accident_count"]
)


# ============================================================
# CITY-RELATIVE PERCENTILES
# ============================================================

print(
    "\nCalculating city-relative percentiles..."
)

metrics = [
    "accident_count",
    "fatality_proportion",
    "total_casualties",
    "mean_risk_score",
]

for metric in metrics:

    percentile_column = (
        f"{metric}_percentile"
    )

    cluster_stats[
        percentile_column
    ] = (
        cluster_stats
        .groupby("city")[metric]
        .rank(
            pct=True,
            method="average"
        )
    )


# ============================================================
# HOTSPOT CANDIDATES
# ============================================================

candidates = cluster_stats[
    cluster_stats["accident_count"]
    >= MIN_ACCIDENTS
].copy()

print(
    f"\nClusters with at least "
    f"{MIN_ACCIDENTS} accidents: "
    f"{len(candidates):,}"
)


# ============================================================
# CITY-RELATIVE RISK FLAGS
# ============================================================

# These are descriptive screening indicators.
#
# Top 25% within the same city is considered elevated
# for that particular indicator.
#
# This avoids directly comparing raw accident counts
# between cities of different spatial distributions.

candidates[
    "high_accident_density"
] = (
    candidates[
        "accident_count_percentile"
    ] >= 0.75
)

candidates[
    "high_fatality_proportion"
] = (
    candidates[
        "fatality_proportion_percentile"
    ] >= 0.75
)

candidates[
    "high_casualty_burden"
] = (
    candidates[
        "total_casualties_percentile"
    ] >= 0.75
)

candidates[
    "high_mean_risk_score"
] = (
    candidates[
        "mean_risk_score_percentile"
    ] >= 0.75
)


# ============================================================
# RISK PROFILE
# ============================================================

def classify_profile(row):
    """
    Descriptive classification based on the number of
    indicators that fall within the top 25% of the
    corresponding city.

    This is NOT a statistical risk score.
    """

    indicators = [
        row["high_accident_density"],
        row["high_fatality_proportion"],
        row["high_casualty_burden"],
        row["high_mean_risk_score"],
    ]

    count = sum(indicators)

    if count >= 3:
        return "multiple_high_risk_indicators"

    if count == 2:
        return "two_high_risk_indicators"

    if count == 1:
        return "single_high_risk_indicator"

    return "no_top_quartile_indicator"


candidates[
    "risk_profile"
] = candidates.apply(
    classify_profile,
    axis=1
)


# ============================================================
# OVERALL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("OVERALL HOTSPOT RISK SUMMARY")
print("=" * 70)

print(
    f"\nDBSCAN spatial clusters: "
    f"{len(cluster_stats):,}"
)

print(
    f"Hotspot candidates "
    f"(>= {MIN_ACCIDENTS} accidents): "
    f"{len(candidates):,}"
)

print("\nRisk profile distribution:")

print(
    candidates[
        "risk_profile"
    ]
    .value_counts()
    .to_string()
)


# ============================================================
# CITY-WISE SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("CITY-WISE HOTSPOT RISK SUMMARY")
print("=" * 70)

city_summary = (
    candidates
    .groupby("city")
    .agg(
        hotspot_candidates=(
            "dbscan_cluster",
            "count"
        ),

        mean_accidents=(
            "accident_count",
            "mean"
        ),

        max_accidents=(
            "accident_count",
            "max"
        ),

        mean_fatality_proportion=(
            "fatality_proportion",
            "mean"
        ),

        max_fatality_proportion=(
            "fatality_proportion",
            "max"
        ),

        mean_total_casualties=(
            "total_casualties",
            "mean"
        ),

        max_total_casualties=(
            "total_casualties",
            "max"
        ),

        mean_risk_score=(
            "mean_risk_score",
            "mean"
        ),
    )
    .reset_index()
)

print(
    city_summary
    .to_string(index=False)
)


# ============================================================
# FUNCTION TO PRINT TOP CLUSTERS
# ============================================================

def print_top_clusters(
    data,
    metric,
    title,
    n=15
):

    print("\n" + "-" * 70)
    print(title)
    print("-" * 70)

    columns = [
        "city",
        "dbscan_cluster",
        "accident_count",
        "fatality_proportion",
        "total_casualties",
        "mean_risk_score",
        "risk_profile",
    ]

    result = (
        data
        .sort_values(
            metric,
            ascending=False
        )
        .head(n)
    )

    print(
        result[columns]
        .to_string(index=False)
    )


# ============================================================
# TOP BY ACCIDENT COUNT
# ============================================================

print_top_clusters(
    candidates,
    "accident_count",
    "TOP CLUSTERS BY ACCIDENT COUNT"
)


# ============================================================
# TOP BY FATALITY PROPORTION
# ============================================================

print_top_clusters(
    candidates,
    "fatality_proportion",
    "TOP CLUSTERS BY FATALITY PROPORTION"
)


# ============================================================
# TOP BY TOTAL CASUALTIES
# ============================================================

print_top_clusters(
    candidates,
    "total_casualties",
    "TOP CLUSTERS BY TOTAL CASUALTIES"
)


# ============================================================
# TOP BY EXISTING RISK SCORE
# ============================================================

print_top_clusters(
    candidates,
    "mean_risk_score",
    "TOP CLUSTERS BY MEAN EXISTING RISK SCORE"
)


# ============================================================
# MULTIPLE-INDICATOR CLUSTERS
# ============================================================

multi_indicator = candidates[
    candidates["risk_profile"]
    == "multiple_high_risk_indicators"
].copy()

print("\n" + "=" * 70)
print("CLUSTERS WITH MULTIPLE HIGH-RISK INDICATORS")
print("=" * 70)

print(
    f"\nNumber of clusters: "
    f"{len(multi_indicator)}"
)

if len(multi_indicator) > 0:

    display_columns = [
        "city",
        "dbscan_cluster",
        "accident_count",
        "fatality_proportion",
        "total_casualties",
        "mean_risk_score",
        "accident_count_percentile",
        "fatality_proportion_percentile",
        "total_casualties_percentile",
        "mean_risk_score_percentile",
    ]

    print(
        multi_indicator
        .sort_values(
            [
                "fatality_proportion",
                "total_casualties",
            ],
            ascending=False
        )[display_columns]
        .to_string(index=False)
    )

else:

    print(
        "\nNo clusters met the "
        "multiple-indicator criterion."
    )


# ============================================================
# ADD INTERPRETATION FLAGS
# ============================================================

# These flags make the CSV easier to use later
# for mapping and analysis.

candidates[
    "priority_for_mapping"
] = (
    candidates["risk_profile"]
    != "no_top_quartile_indicator"
)


# ============================================================
# SORT RESULTS
# ============================================================

candidates = candidates.sort_values(
    [
        "city",
        "risk_profile",
        "accident_count",
    ],
    ascending=[
        True,
        True,
        False,
    ]
)


# ============================================================
# OUTPUT FILES
# ============================================================

all_results_file = (
    OUTPUT_DIR
    / "hotspot_risk_analysis.csv"
)

candidate_file = (
    OUTPUT_DIR
    / "hotspot_risk_candidates.csv"
)

city_file = (
    OUTPUT_DIR
    / "hotspot_risk_city_summary.csv"
)


# Save all DBSCAN clusters
cluster_stats.to_csv(
    all_results_file,
    index=False
)

# Save clusters meeting minimum accident threshold
candidates.to_csv(
    candidate_file,
    index=False
)

# Save city-level summary
city_summary.to_csv(
    city_file,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("OUTPUT FILES")
print("=" * 70)

print(
    f"\n1. {all_results_file}"
)

print(
    f"2. {candidate_file}"
)

print(
    f"3. {city_file}"
)

print("\nHotspot risk analysis completed successfully.")

print("=" * 70)