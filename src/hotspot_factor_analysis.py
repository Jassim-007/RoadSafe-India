"""
RoadSafe India
Hotspot Factor Analysis

Purpose:
    Analyze road, traffic, environmental and temporal
    characteristics of DBSCAN hotspot candidates.

    Focus:
    - Multiple-indicator hotspot clusters
    - Comparison with other DBSCAN clusters
    - Descriptive factor distributions

Important:
    This analysis describes associations in the dataset.
    It does not establish causal relationships.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

ACCIDENT_FILE = (
    BASE_DIR
    / "outputs"
    / "clusters"
    / "final_clustered_accidents.csv"
)

RISK_FILE = (
    BASE_DIR
    / "outputs"
    / "clusters"
    / "hotspot_risk_candidates.csv"
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
# LOAD DATA
# ============================================================

print("=" * 70)
print("ROADSAFE INDIA - HOTSPOT FACTOR ANALYSIS")
print("=" * 70)

print("\nLoading accident data...")

df = pd.read_csv(ACCIDENT_FILE)

print(
    f"Accident records loaded: "
    f"{len(df):,}"
)

print("\nLoading hotspot-risk analysis...")

risk = pd.read_csv(RISK_FILE)

print(
    f"Hotspot candidate clusters: "
    f"{len(risk):,}"
)


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_accident_columns = [
    "city",
    "dbscan_cluster",
    "accident_severity",
    "road_type",
    "traffic_signal",
    "weather",
    "traffic_density",
    "cause",
    "is_peak_hour",
    "is_weekend",
    "vehicles_involved",
    "casualties",
    "risk_score",
]

missing = [
    col
    for col in required_accident_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing accident columns: {missing}"
    )


# ============================================================
# IDENTIFY MULTIPLE-INDICATOR HOTSPOTS
# ============================================================

hotspot_clusters = risk[
    risk["risk_profile"]
    == "multiple_high_risk_indicators"
].copy()

print(
    "\nMultiple-indicator hotspot clusters: "
    f"{len(hotspot_clusters):,}"
)


# ============================================================
# GET ACCIDENT RECORDS FOR HOTSPOTS
# ============================================================

hotspot_keys = hotspot_clusters[
    [
        "city",
        "dbscan_cluster"
    ]
].drop_duplicates()

hotspot_records = df.merge(
    hotspot_keys,
    on=[
        "city",
        "dbscan_cluster"
    ],
    how="inner"
)

print(
    "Accident records inside "
    "multiple-indicator hotspots: "
    f"{len(hotspot_records):,}"
)


# ============================================================
# ADD COMPARISON GROUP
# ============================================================

hotspot_key_set = set(
    zip(
        hotspot_keys["city"],
        hotspot_keys["dbscan_cluster"]
    )
)

df["analysis_group"] = [
    "multiple_indicator_hotspot"
    if (city, cluster) in hotspot_key_set
    else "other_clustered_accident"
    for city, cluster
    in zip(
        df["city"],
        df["dbscan_cluster"]
    )
]

# Remove DBSCAN noise from comparison.
df_clustered = df[
    df["dbscan_cluster"] != -1
].copy()

print(
    "\nClustered records available for comparison: "
    f"{len(df_clustered):,}"
)


# ============================================================
# FUNCTION: DISTRIBUTION TABLE
# ============================================================

def categorical_distribution(
    data,
    column,
    group_column="analysis_group"
):

    table = pd.crosstab(
        data[group_column],
        data[column],
        normalize="index"
    ) * 100

    return table.round(2)


# ============================================================
# CATEGORICAL FACTORS
# ============================================================

categorical_factors = [
    "road_type",
    "traffic_signal",
    "weather",
    "traffic_density",
    "cause",
    "is_peak_hour",
    "is_weekend",
    "accident_severity",
]


print("\n" + "=" * 70)
print("FACTOR DISTRIBUTIONS")
print("=" * 70)


factor_tables = {}


for factor in categorical_factors:

    print("\n" + "-" * 70)
    print(factor.upper())
    print("-" * 70)

    table = categorical_distribution(
        df_clustered,
        factor
    )

    factor_tables[factor] = table

    print(table)


# ============================================================
# SAVE FACTOR TABLES
# ============================================================

for factor, table in factor_tables.items():

    output_file = (
        OUTPUT_DIR
        / f"hotspot_factor_{factor}.csv"
    )

    table.to_csv(output_file)


# ============================================================
# NUMERICAL COMPARISON
# ============================================================

print("\n" + "=" * 70)
print("NUMERICAL CHARACTERISTICS")
print("=" * 70)

numeric_columns = [
    "casualties",
    "vehicles_involved",
    "risk_score",
]

numeric_summary = (
    df_clustered
    .groupby("analysis_group")[
        numeric_columns
    ]
    .agg(
        [
            "count",
            "mean",
            "median",
            "std",
        ]
    )
    .round(4)
)

print(
    numeric_summary.to_string()
)

numeric_summary.to_csv(
    OUTPUT_DIR
    / "hotspot_factor_numeric_summary.csv"
)


# ============================================================
# CITY-WISE HOTSPOT FACTORS
# ============================================================

print("\n" + "=" * 70)
print("CITY-WISE MULTIPLE-INDICATOR HOTSPOT FACTORS")
print("=" * 70)


city_hotspot_summary = (
    hotspot_records
    .groupby("city")
    .agg(
        accident_records=(
            "dbscan_cluster",
            "size"
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

        fatality_proportion=(
            "accident_severity",
            lambda x:
            (x == "fatal").mean()
        ),

        major_proportion=(
            "accident_severity",
            lambda x:
            (x == "major").mean()
        ),

        peak_hour_proportion=(
            "is_peak_hour",
            "mean"
        ),

        weekend_proportion=(
            "is_weekend",
            "mean"
        ),
    )
    .reset_index()
)


# Convert proportions to percentages
for column in [
    "fatality_proportion",
    "major_proportion",
    "peak_hour_proportion",
    "weekend_proportion",
]:

    city_hotspot_summary[column] *= 100


city_hotspot_summary = (
    city_hotspot_summary
    .round(2)
)

print(
    city_hotspot_summary
    .to_string(index=False)
)

city_hotspot_summary.to_csv(
    OUTPUT_DIR
    / "hotspot_factor_city_summary.csv",
    index=False
)


# ============================================================
# TOP CAUSES IN MULTIPLE-INDICATOR HOTSPOTS
# ============================================================

print("\n" + "=" * 70)
print("CAUSE DISTRIBUTION IN MULTIPLE-INDICATOR HOTSPOTS")
print("=" * 70)

cause_hotspots = (
    hotspot_records["cause"]
    .value_counts(normalize=True)
    * 100
)

cause_hotspots = (
    cause_hotspots
    .round(2)
)

print(
    cause_hotspots.to_string()
)

cause_hotspots.to_csv(
    OUTPUT_DIR
    / "hotspot_cause_distribution.csv"
)


# ============================================================
# ROAD TYPE DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("ROAD TYPE DISTRIBUTION IN MULTIPLE-INDICATOR HOTSPOTS")
print("=" * 70)

road_hotspots = (
    hotspot_records["road_type"]
    .value_counts(normalize=True)
    * 100
).round(2)

print(
    road_hotspots.to_string()
)

road_hotspots.to_csv(
    OUTPUT_DIR
    / "hotspot_road_type_distribution.csv"
)


# ============================================================
# WEATHER DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("WEATHER DISTRIBUTION IN MULTIPLE-INDICATOR HOTSPOTS")
print("=" * 70)

weather_hotspots = (
    hotspot_records["weather"]
    .value_counts(normalize=True)
    * 100
).round(2)

print(
    weather_hotspots.to_string()
)

weather_hotspots.to_csv(
    OUTPUT_DIR
    / "hotspot_weather_distribution.csv"
)


# ============================================================
# TRAFFIC DENSITY DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("TRAFFIC DENSITY DISTRIBUTION IN MULTIPLE-INDICATOR HOTSPOTS")
print("=" * 70)

traffic_hotspots = (
    hotspot_records["traffic_density"]
    .value_counts(normalize=True)
    * 100
).round(2)

print(
    traffic_hotspots.to_string()
)

traffic_hotspots.to_csv(
    OUTPUT_DIR
    / "hotspot_traffic_density_distribution.csv"
)


# ============================================================
# SEVERITY DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("SEVERITY DISTRIBUTION IN MULTIPLE-INDICATOR HOTSPOTS")
print("=" * 70)

severity_hotspots = (
    hotspot_records["accident_severity"]
    .value_counts(normalize=True)
    * 100
).round(2)

print(
    severity_hotspots.to_string()
)

severity_hotspots.to_csv(
    OUTPUT_DIR
    / "hotspot_severity_distribution.csv"
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("HOTSPOT FACTOR ANALYSIS COMPLETED")
print("=" * 70)

print(
    "\nOutputs saved in:"
)

print(
    OUTPUT_DIR
)

print(
    "\nNext stage: spatial hotspot mapping."
)

print("=" * 70)