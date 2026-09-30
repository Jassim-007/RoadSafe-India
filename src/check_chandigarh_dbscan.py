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
    / "dbscan_fine_tuning_results.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "clusters"
    / "chandigarh_parameter_analysis.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Could not find:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

# Keep only Chandigarh.
ch = df[
    df["city"].str.lower() == "chandigarh"
].copy()

if ch.empty:
    raise ValueError(
        "No Chandigarh records found in fine-tuning results."
    )


# ============================================================
# CALCULATE DIAGNOSTICS
# ============================================================

ch["largest_cluster_proportion"] = (
    ch["largest_cluster"] / ch["records"]
)

ch["clustered_percentage"] = (
    ch["clustered_count"] / ch["records"] * 100
)


# ============================================================
# SORT
# ============================================================

ch = ch.sort_values(
    ["min_samples", "eps_km"]
).reset_index(drop=True)


# ============================================================
# PRINT OVERVIEW
# ============================================================

print("=" * 80)
print("CHANDIGARH DBSCAN PARAMETER ANALYSIS")
print("=" * 80)

print(
    f"\nTotal configurations tested: {len(ch)}"
)

print(
    f"Records in Chandigarh: "
    f"{int(ch['records'].iloc[0]):,}"
)

print(
    f"eps range: "
    f"{ch['eps_km'].min():.2f} - "
    f"{ch['eps_km'].max():.2f} km"
)

print(
    f"min_samples values: "
    f"{sorted(ch['min_samples'].unique())}"
)


# ============================================================
# FULL PARAMETER TABLE
# ============================================================

print("\n" + "=" * 80)
print("ALL CHANDIGARH CONFIGURATIONS")
print("=" * 80)

display_columns = [
    "eps_km",
    "min_samples",
    "clusters",
    "noise_percentage",
    "largest_cluster",
    "largest_cluster_proportion",
    "median_cluster_size",
]

print(
    ch[display_columns].to_string(
        index=False
    )
)


# ============================================================
# BEST CONFIGURATIONS BY DIFFERENT CRITERIA
# ============================================================

print("\n" + "=" * 80)
print("CONFIGURATIONS WITH SMALLEST LARGEST-CLUSTER SHARE")
print("=" * 80)

smallest_largest = (
    ch.sort_values(
        "largest_cluster_proportion"
    )
    .head(15)
)

print(
    smallest_largest[display_columns].to_string(
        index=False
    )
)


# ============================================================
# CONFIGURATIONS WITH MODERATE NOISE
# ============================================================

print("\n" + "=" * 80)
print("CONFIGURATIONS WITH 5%-30% NOISE")
print("=" * 80)

moderate_noise = ch[
    (ch["noise_percentage"] >= 5)
    & (ch["noise_percentage"] <= 30)
].copy()

if moderate_noise.empty:

    print(
        "No Chandigarh configurations fall "
        "within the 5%-30% noise range."
    )

else:

    print(
        moderate_noise[display_columns]
        .sort_values(
            "largest_cluster_proportion"
        )
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# CONFIGURATIONS WITH NO DOMINANT CLUSTER
# ============================================================

print("\n" + "=" * 80)
print("CONFIGURATIONS WITH LARGEST CLUSTER <= 50%")
print("=" * 80)

non_dominant = ch[
    ch["largest_cluster_proportion"] <= 0.50
].copy()

if non_dominant.empty:

    print(
        "No tested configuration has a largest "
        "cluster containing <= 50% of records."
    )

else:

    print(
        non_dominant[display_columns]
        .sort_values(
            "largest_cluster_proportion"
        )
        .to_string(index=False)
    )


# ============================================================
# BEST BALANCED CONFIGURATIONS
# ============================================================

print("\n" + "=" * 80)
print("BALANCED CONFIGURATION SEARCH")
print("=" * 80)

# This is only a diagnostic ranking.
#
# We want:
# - reasonable cluster count
# - moderate noise
# - small largest cluster
# - reasonable median cluster size

balanced = ch.copy()

balanced["diagnostic_score"] = (

    # Penalize dominant clusters.
    (1 - balanced["largest_cluster_proportion"]) * 4

    # Prefer moderate noise.
    + (
        1
        - abs(
            balanced["noise_percentage"] - 15
        ) / 30
    )

    # Prefer a useful number of clusters.
    + np.log1p(
        balanced["clusters"]
    ) / np.log1p(100)

    # Prefer larger median clusters.
    + np.log1p(
        balanced["median_cluster_size"]
    ) / np.log1p(100)
)

balanced = balanced.sort_values(
    "diagnostic_score",
    ascending=False
)

print(
    balanced[
        display_columns
        + ["diagnostic_score"]
    ]
    .head(15)
    .to_string(index=False)
)


# ============================================================
# EPS TREND SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("EPS TREND SUMMARY")
print("=" * 80)

for min_samples in sorted(
    ch["min_samples"].unique()
):

    subset = ch[
        ch["min_samples"] == min_samples
    ].copy()

    print(
        f"\nmin_samples = {min_samples}"
    )

    print(
        subset[
            [
                "eps_km",
                "clusters",
                "noise_percentage",
                "largest_cluster_proportion",
                "median_cluster_size",
            ]
        ].to_string(
            index=False
        )
    )


# ============================================================
# SAVE ANALYSIS
# ============================================================

ch.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 80)
print("ANALYSIS SAVED")
print("=" * 80)

print(OUTPUT_FILE)

print("\nChandigarh analysis complete.")