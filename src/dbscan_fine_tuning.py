import os
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

INPUT_FILE = "data/processed/indian_accidents_clean.csv"
OUTPUT_DIR = "outputs/clusters"

os.makedirs(OUTPUT_DIR, exist_ok=True)

EARTH_RADIUS_KM = 6371.0088

# Fine eps values
EPS_VALUES_KM = np.round(
    np.arange(0.90, 2.11, 0.05),
    2
)

# Test several density requirements
MIN_SAMPLES_VALUES = [8, 10, 12, 15]


df = pd.read_csv(INPUT_FILE)

df["lat_rad"] = np.radians(df["latitude"])
df["lon_rad"] = np.radians(df["longitude"])

results = []


for city in sorted(df["city"].unique()):

    city_df = df[df["city"] == city].copy()

    coordinates = city_df[
        ["lat_rad", "lon_rad"]
    ].to_numpy()

    print("\n" + "=" * 70)
    print(f"{city} | {len(city_df):,} records")
    print("=" * 70)

    for min_samples in MIN_SAMPLES_VALUES:

        for eps_km in EPS_VALUES_KM:

            eps_radians = eps_km / EARTH_RADIUS_KM

            model = DBSCAN(
                eps=eps_radians,
                min_samples=min_samples,
                metric="haversine",
                algorithm="ball_tree",
                n_jobs=-1
            )

            labels = model.fit_predict(coordinates)

            cluster_labels = set(labels)

            if -1 in cluster_labels:
                cluster_labels.remove(-1)

            n_clusters = len(cluster_labels)

            noise_count = np.sum(labels == -1)

            noise_percentage = (
                noise_count / len(labels)
            ) * 100

            clustered_count = len(labels) - noise_count

            if n_clusters > 0:

                sizes = pd.Series(labels)
                sizes = sizes[sizes != -1].value_counts()

                largest_cluster = int(sizes.max())
                smallest_cluster = int(sizes.min())
                median_cluster = float(sizes.median())

            else:

                largest_cluster = 0
                smallest_cluster = 0
                median_cluster = 0

            results.append({
                "city": city,
                "records": len(city_df),
                "eps_km": eps_km,
                "min_samples": min_samples,
                "clusters": n_clusters,
                "noise_count": int(noise_count),
                "noise_percentage": round(
                    noise_percentage, 2
                ),
                "clustered_count": int(
                    clustered_count
                ),
                "clustered_percentage": round(
                    clustered_count / len(labels) * 100,
                    2
                ),
                "largest_cluster": largest_cluster,
                "smallest_cluster": smallest_cluster,
                "median_cluster_size": median_cluster
            })


results_df = pd.DataFrame(results)

output_file = os.path.join(
    OUTPUT_DIR,
    "dbscan_fine_tuning_results.csv"
)

results_df.to_csv(
    output_file,
    index=False
)

print("\n" + "=" * 70)
print("FINE-TUNING COMPLETED")
print("=" * 70)

print(
    f"Total combinations: {len(results_df):,}"
)

print(f"Saved to: {output_file}")


# --------------------------------------------------
# Show potentially useful candidates
# --------------------------------------------------

print("\nPotential candidate configurations:")
print(
    "(2-100 clusters and 2%-40% noise)"
)

candidates = results_df[
    (results_df["clusters"] >= 2) &
    (results_df["clusters"] <= 100) &
    (results_df["noise_percentage"] >= 2) &
    (results_df["noise_percentage"] <= 40)
]

for city in sorted(candidates["city"].unique()):

    city_candidates = candidates[
        candidates["city"] == city
    ]

    print("\n" + "-" * 70)
    print(city)

    print(
        city_candidates[
            [
                "eps_km",
                "min_samples",
                "clusters",
                "noise_percentage",
                "largest_cluster",
                "median_cluster_size"
            ]
        ].to_string(index=False)
    )