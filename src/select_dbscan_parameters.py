from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "clusters"
    / "dbscan_fine_tuning_results.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "clusters"
    / "final_dbscan_parameters.csv"
)


# ============================================================
# CITIES
# ============================================================

EXCLUDED_CITIES = {
    "Chandigarh": (
        "Excluded from DBSCAN because none of the tested "
        "configurations produced sufficiently separated "
        "spatial clusters."
    )
}


# ============================================================
# LOAD RESULTS
# ============================================================

if not RESULTS_FILE.exists():
    raise FileNotFoundError(
        f"Could not find:\n{RESULTS_FILE}"
    )

df = pd.read_csv(RESULTS_FILE)

print("=" * 70)
print("FINAL DBSCAN PARAMETER SELECTION")
print("=" * 70)

print(f"\nLoaded configurations: {len(df):,}")
print(f"Cities in dataset: {df['city'].nunique()}")


# ============================================================
# STANDARDIZE COLUMN NAMES
# ============================================================

df.columns = [
    column.strip().lower()
    for column in df.columns
]


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = {
    "city",
    "records",
    "eps_km",
    "min_samples",
    "clusters",
    "noise_percentage",
    "largest_cluster",
    "median_cluster_size",
}

missing = required_columns - set(df.columns)

if missing:
    raise ValueError(
        f"Missing required columns: {sorted(missing)}"
    )


# ============================================================
# CALCULATE DIAGNOSTICS
# ============================================================

df["largest_cluster_proportion"] = (
    df["largest_cluster"] / df["records"]
)


# ============================================================
# SCREENING CRITERIA
# ============================================================

# These are practical screening criteria, not mathematical
# definitions of a valid DBSCAN solution.

MIN_CLUSTERS = 3
MAX_CLUSTERS = 100

MAX_NOISE_PERCENTAGE = 40.0

MAX_LARGEST_CLUSTER_PROPORTION = 0.70


df["passes_screen"] = (
    (df["clusters"] >= MIN_CLUSTERS)
    & (df["clusters"] <= MAX_CLUSTERS)
    & (df["noise_percentage"] <= MAX_NOISE_PERCENTAGE)
    & (
        df["largest_cluster_proportion"]
        <= MAX_LARGEST_CLUSTER_PROPORTION
    )
)


# ============================================================
# STABILITY
# ============================================================

df = df.sort_values(
    ["city", "min_samples", "eps_km"]
).reset_index(drop=True)


df["cluster_change"] = (
    df.groupby(
        ["city", "min_samples"]
    )["clusters"]
    .diff()
    .abs()
)


df["noise_change"] = (
    df.groupby(
        ["city", "min_samples"]
    )["noise_percentage"]
    .diff()
    .abs()
)


df["relative_cluster_change"] = (
    df["cluster_change"]
    / df["clusters"].replace(0, np.nan)
)


df["stability_score"] = (
    df["relative_cluster_change"].fillna(0)
    + df["noise_change"].fillna(0) / 100
)


# ============================================================
# SELECTION SCORE
# ============================================================

df["selection_score"] = 0.0


# Lower noise is generally preferable.
df["selection_score"] += (
    (40 - df["noise_percentage"].clip(upper=40))
    / 40
) * 2


# Prefer a useful number of clusters without rewarding
# extremely large cluster counts too aggressively.
df["selection_score"] += (
    np.log1p(df["clusters"])
    / np.log1p(MAX_CLUSTERS)
) * 1.5


# Penalize dominant clusters.
df["selection_score"] -= (
    df["largest_cluster_proportion"]
    * 3
)


# Prefer stable parameter regions.
df["selection_score"] -= (
    df["stability_score"].clip(upper=2)
)


# ============================================================
# SELECT PARAMETERS
# ============================================================

selected_rows = []

print("\n" + "=" * 70)
print("CITY-WISE FINAL SELECTION")
print("=" * 70)


for city in sorted(df["city"].unique()):

    # --------------------------------------------------------
    # EXCLUDED CITY
    # --------------------------------------------------------

    if city in EXCLUDED_CITIES:

        print(f"\n{city}")
        print("-" * 50)
        print("DBSCAN STATUS : EXCLUDED")
        print(
            f"REASON        : "
            f"{EXCLUDED_CITIES[city]}"
        )

        selected_rows.append({
            "city": city,
            "dbscan_status": "excluded",
            "reason": EXCLUDED_CITIES[city],
            "eps_km": np.nan,
            "min_samples": np.nan,
            "clusters": np.nan,
            "noise_percentage": np.nan,
            "records": int(
                df[df["city"] == city]["records"].iloc[0]
            ),
            "largest_cluster": np.nan,
            "largest_cluster_proportion": np.nan,
            "median_cluster_size": np.nan,
            "stability_score": np.nan,
            "selection_score": np.nan,
        })

        continue


    # --------------------------------------------------------
    # NORMAL CITY
    # --------------------------------------------------------

    city_df = df[
        df["city"] == city
    ].copy()


    valid = city_df[
        city_df["passes_screen"]
    ].copy()


    if valid.empty:

        print(f"\n{city}")
        print("-" * 50)
        print(
            "WARNING: No configuration passed "
            "the screening criteria."
        )

        # Do not silently force a parameter.
        selected_rows.append({
            "city": city,
            "dbscan_status": "review_required",
            "reason": (
                "No tested configuration passed "
                "the DBSCAN screening criteria."
            ),
            "eps_km": np.nan,
            "min_samples": np.nan,
            "clusters": np.nan,
            "noise_percentage": np.nan,
            "records": int(
                city_df["records"].iloc[0]
            ),
            "largest_cluster": np.nan,
            "largest_cluster_proportion": np.nan,
            "median_cluster_size": np.nan,
            "stability_score": np.nan,
            "selection_score": np.nan,
        })

        continue


    # Highest scoring valid configuration.
    valid = valid.sort_values(
        "selection_score",
        ascending=False
    )

    best = valid.iloc[0]


    selected_rows.append({
        "city": city,
        "dbscan_status": "selected",
        "reason": (
            "Configuration passed screening "
            "and was selected using the "
            "parameter-selection diagnostics."
        ),
        "eps_km": best["eps_km"],
        "min_samples": int(best["min_samples"]),
        "clusters": int(best["clusters"]),
        "noise_percentage": best["noise_percentage"],
        "records": int(best["records"]),
        "largest_cluster": int(
            best["largest_cluster"]
        ),
        "largest_cluster_proportion":
            best["largest_cluster_proportion"],
        "median_cluster_size":
            best["median_cluster_size"],
        "stability_score":
            best["stability_score"],
        "selection_score":
            best["selection_score"],
    })


    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    print(f"\n{city}")
    print("-" * 50)

    print("DBSCAN STATUS      : SELECTED")

    print(
        f"eps                : "
        f"{best['eps_km']:.2f} km"
    )

    print(
        f"min_samples        : "
        f"{int(best['min_samples'])}"
    )

    print(
        f"clusters            : "
        f"{int(best['clusters'])}"
    )

    print(
        f"noise               : "
        f"{best['noise_percentage']:.2f}%"
    )

    print(
        f"largest cluster     : "
        f"{int(best['largest_cluster']):,}"
    )

    print(
        f"largest cluster %   : "
        f"{best['largest_cluster_proportion'] * 100:.2f}%"
    )

    print(
        f"median cluster size : "
        f"{best['median_cluster_size']:.1f}"
    )

    print(
        f"stability score     : "
        f"{best['stability_score']:.3f}"
    )

    print(
        f"selection score     : "
        f"{best['selection_score']:.3f}"
    )


# ============================================================
# CREATE FINAL TABLE
# ============================================================

final_params = pd.DataFrame(
    selected_rows
)


final_params = final_params.sort_values(
    "city"
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

final_params.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# PRINT FINAL TABLE
# ============================================================

print("\n" + "=" * 70)
print("FINAL PARAMETER TABLE")
print("=" * 70)

print(
    final_params.to_string(
        index=False
    )
)


print("\n" + "=" * 70)
print("SAVED")
print("=" * 70)

print(OUTPUT_FILE)

print("\nFinal parameter selection complete.")