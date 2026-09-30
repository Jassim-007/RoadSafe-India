from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.cluster import DBSCAN


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "indian_accidents_clean.csv"
)

PARAMETER_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "clusters"
    / "final_dbscan_parameters.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "clusters"
)

CLUSTERED_FILE = (
    OUTPUT_DIR
    / "final_clustered_accidents.csv"
)

SUMMARY_FILE = (
    OUTPUT_DIR
    / "cluster_summary.csv"
)

CITY_SUMMARY_FILE = (
    OUTPUT_DIR
    / "cluster_city_summary.csv"
)


# ============================================================
# SETTINGS
# ============================================================

EARTH_RADIUS_KM = 6371.0088

LATITUDE_COLUMN = "latitude"
LONGITUDE_COLUMN = "longitude"

CITY_COLUMN = "city"


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
print("FINAL DBSCAN CLUSTERING")
print("=" * 75)

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Accident dataset not found:\n{DATA_FILE}"
    )

if not PARAMETER_FILE.exists():
    raise FileNotFoundError(
        f"Parameter file not found:\n{PARAMETER_FILE}"
    )


df = pd.read_csv(DATA_FILE)

parameters = pd.read_csv(
    PARAMETER_FILE
)


print(
    f"\nAccident records loaded: "
    f"{len(df):,}"
)

print(
    f"Parameter records loaded: "
    f"{len(parameters):,}"
)


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_data_columns = {
    CITY_COLUMN,
    LATITUDE_COLUMN,
    LONGITUDE_COLUMN,
}

missing_data = (
    required_data_columns
    - set(df.columns)
)

if missing_data:
    raise ValueError(
        f"Missing accident-data columns: "
        f"{sorted(missing_data)}"
    )


required_parameter_columns = {
    "city",
    "dbscan_status",
    "eps_km",
    "min_samples",
}

missing_parameters = (
    required_parameter_columns
    - set(parameters.columns)
)

if missing_parameters:
    raise ValueError(
        f"Missing parameter columns: "
        f"{sorted(missing_parameters)}"
    )


# ============================================================
# INITIALIZE OUTPUT COLUMNS
# ============================================================

# -1 is the conventional DBSCAN noise label.

df["dbscan_cluster"] = -1

df["dbscan_status"] = "not_processed"

df["dbscan_eps_km"] = np.nan

df["dbscan_min_samples"] = np.nan


# ============================================================
# PROCESS EACH CITY
# ============================================================

selected_parameters = parameters[
    parameters["dbscan_status"] == "selected"
].copy()


selected_parameters = selected_parameters[
    selected_parameters["eps_km"].notna()
    & selected_parameters["min_samples"].notna()
]


print("\n" + "=" * 75)
print("CITY-WISE DBSCAN")
print("=" * 75)


global_cluster_offset = 0

city_results = []


for _, parameter_row in selected_parameters.iterrows():

    city = parameter_row["city"]

    eps_km = float(
        parameter_row["eps_km"]
    )

    min_samples = int(
        parameter_row["min_samples"]
    )


    # --------------------------------------------------------
    # CITY DATA
    # --------------------------------------------------------

    city_mask = (
        df[CITY_COLUMN] == city
    )

    city_indices = df.index[
        city_mask
    ]

    city_df = df.loc[
        city_indices
    ].copy()


    if city_df.empty:

        print(
            f"\nWARNING: No records found for {city}"
        )

        continue


    # --------------------------------------------------------
    # COORDINATES
    # --------------------------------------------------------

    coordinates = city_df[
        [
            LATITUDE_COLUMN,
            LONGITUDE_COLUMN,
        ]
    ].to_numpy(
        dtype=float
    )


    # Convert degrees → radians because sklearn's
    # Haversine metric expects radians.
    coordinates_radians = np.radians(
        coordinates
    )


    # Convert kilometers → radians.
    eps_radians = (
        eps_km
        / EARTH_RADIUS_KM
    )


    # --------------------------------------------------------
    # DBSCAN
    # --------------------------------------------------------

    model = DBSCAN(
        eps=eps_radians,
        min_samples=min_samples,
        metric="haversine",
        algorithm="ball_tree",
        n_jobs=-1,
    )


    labels = model.fit_predict(
        coordinates_radians
    )


    # --------------------------------------------------------
    # MAKE CLUSTER IDS UNIQUE ACROSS CITIES
    # --------------------------------------------------------

    city_labels = labels.copy()

    valid_labels = sorted(
        label
        for label in np.unique(labels)
        if label != -1
    )


    label_mapping = {}

    for label in valid_labels:

        label_mapping[label] = (
            global_cluster_offset
        )

        global_cluster_offset += 1


    for local_label, global_label in (
        label_mapping.items()
    ):

        city_labels[
            labels == local_label
        ] = global_label


    # --------------------------------------------------------
    # SAVE RESULTS TO MAIN DATAFRAME
    # --------------------------------------------------------

    df.loc[
        city_indices,
        "dbscan_cluster"
    ] = city_labels


    df.loc[
        city_indices,
        "dbscan_status"
    ] = "clustered"


    df.loc[
        city_indices,
        "dbscan_eps_km"
    ] = eps_km


    df.loc[
        city_indices,
        "dbscan_min_samples"
    ] = min_samples


    # --------------------------------------------------------
    # CITY STATISTICS
    # --------------------------------------------------------

    clustered_mask = (
        labels != -1
    )

    noise_count = int(
        np.sum(labels == -1)
    )

    clustered_count = int(
        np.sum(clustered_mask)
    )


    unique_clusters = [
        label
        for label in np.unique(labels)
        if label != -1
    ]


    cluster_count = len(
        unique_clusters
    )


    noise_percentage = (
        noise_count
        / len(labels)
        * 100
    )


    # Largest cluster.
    if cluster_count > 0:

        cluster_sizes = pd.Series(
            labels[clustered_mask]
        ).value_counts()

        largest_cluster_size = int(
            cluster_sizes.max()
        )

        median_cluster_size = float(
            cluster_sizes.median()
        )

    else:

        largest_cluster_size = 0
        median_cluster_size = 0


    city_results.append({
        "city": city,
        "records": len(city_df),
        "eps_km": eps_km,
        "min_samples": min_samples,
        "clusters": cluster_count,
        "noise_count": noise_count,
        "noise_percentage":
            noise_percentage,
        "clustered_count":
            clustered_count,
        "clustered_percentage":
            clustered_count
            / len(city_df)
            * 100,
        "largest_cluster":
            largest_cluster_size,
        "median_cluster_size":
            median_cluster_size,
    })


    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    print(f"\n{city}")
    print("-" * 50)

    print(
        f"Records             : "
        f"{len(city_df):,}"
    )

    print(
        f"eps                 : "
        f"{eps_km:.2f} km"
    )

    print(
        f"min_samples         : "
        f"{min_samples}"
    )

    print(
        f"Clusters            : "
        f"{cluster_count}"
    )

    print(
        f"Noise records       : "
        f"{noise_count:,}"
    )

    print(
        f"Noise percentage    : "
        f"{noise_percentage:.2f}%"
    )

    print(
        f"Largest cluster     : "
        f"{largest_cluster_size:,}"
    )

    print(
        f"Median cluster size : "
        f"{median_cluster_size:.1f}"
    )


# ============================================================
# MARK EXCLUDED CITIES
# ============================================================

excluded_parameters = parameters[
    parameters["dbscan_status"] != "selected"
]


for _, parameter_row in (
    excluded_parameters.iterrows()
):

    city = parameter_row["city"]

    mask = (
        df[CITY_COLUMN] == city
    )

    df.loc[
        mask,
        "dbscan_status"
    ] = "excluded"


    df.loc[
        mask,
        "dbscan_cluster"
    ] = -1


# ============================================================
# SAVE CLUSTERED DATASET
# ============================================================

df.to_csv(
    CLUSTERED_FILE,
    index=False
)


# ============================================================
# CREATE CITY SUMMARY
# ============================================================

city_summary = pd.DataFrame(
    city_results
)

city_summary.to_csv(
    CITY_SUMMARY_FILE,
    index=False
)


# ============================================================
# CREATE CLUSTER SUMMARY
# ============================================================

clustered_records = df[
    (df["dbscan_status"] == "clustered")
    & (df["dbscan_cluster"] != -1)
].copy()


if not clustered_records.empty:

    cluster_summary = (
        clustered_records
        .groupby(
            [
                "dbscan_cluster",
                "city",
            ]
        )
        .agg(
            accident_count=(
                "accident_id",
                "count"
            ),
            mean_risk_score=(
                "risk_score",
                "mean"
            ),
            median_risk_score=(
                "risk_score",
                "median"
            ),
            total_casualties=(
                "casualties",
                "sum"
            ),
            mean_casualties=(
                "casualties",
                "mean"
            ),
            fatal_accidents=(
                "accident_severity",
                lambda x:
                (x == "fatal").sum()
            ),
            major_accidents=(
                "accident_severity",
                lambda x:
                (x == "major").sum()
            ),
            minor_accidents=(
                "accident_severity",
                lambda x:
                (x == "minor").sum()
            ),
        )
        .reset_index()
    )


    # Fatal percentage.
    cluster_summary[
        "fatal_percentage"
    ] = (
        cluster_summary[
            "fatal_accidents"
        ]
        / cluster_summary[
            "accident_count"
        ]
        * 100
    )


    # Calculate geographic centroid.
    centroids = (
        clustered_records
        .groupby(
            [
                "dbscan_cluster",
                "city",
            ]
        )
        .agg(
            centroid_latitude=(
                LATITUDE_COLUMN,
                "mean"
            ),
            centroid_longitude=(
                LONGITUDE_COLUMN,
                "mean"
            ),
        )
        .reset_index()
    )


    cluster_summary = cluster_summary.merge(
        centroids,
        on=[
            "dbscan_cluster",
            "city",
        ],
        how="left"
    )


else:

    cluster_summary = pd.DataFrame()


cluster_summary.to_csv(
    SUMMARY_FILE,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 75)
print("FINAL DBSCAN SUMMARY")
print("=" * 75)

print(
    f"\nTotal accident records : "
    f"{len(df):,}"
)

print(
    f"DBSCAN cities          : "
    f"{len(city_results)}"
)

print(
    f"Total spatial clusters : "
    f"{len(cluster_summary):,}"
    if not cluster_summary.empty
    else "Total spatial clusters : 0"
)


print("\nCity summary:")

if not city_summary.empty:

    print(
        city_summary.to_string(
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
    f"\nClustered accident data:"
    f"\n{CLUSTERED_FILE}"
)

print(
    f"\nCluster summary:"
    f"\n{SUMMARY_FILE}"
)

print(
    f"\nCity summary:"
    f"\n{CITY_SUMMARY_FILE}"
)


print("\nFinal DBSCAN clustering complete.")