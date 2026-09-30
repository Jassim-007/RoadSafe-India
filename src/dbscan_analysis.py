import os
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

# --------------------------------------------------
# Paths
# --------------------------------------------------

INPUT_FILE = "data/processed/indian_accidents_clean.csv"
OUTPUT_DIR = "outputs/clusters"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------------------------------
# Parameters to test
# --------------------------------------------------

EPS_VALUES_KM = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
MIN_SAMPLES_VALUES = [5, 10, 15, 20]

EARTH_RADIUS_KM = 6371.0088


# --------------------------------------------------
# Load data
# --------------------------------------------------

print("=" * 70)
print("ROADSAFE INDIA - DBSCAN PARAMETER ANALYSIS")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"\nTotal records: {len(df):,}")
print(f"Cities: {df['city'].nunique()}")


# --------------------------------------------------
# Convert coordinates to radians
# --------------------------------------------------

df["lat_rad"] = np.radians(df["latitude"])
df["lon_rad"] = np.radians(df["longitude"])


# --------------------------------------------------
# Run DBSCAN city-wise
# --------------------------------------------------

results = []

for city in sorted(df["city"].unique()):

    city_df = df[df["city"] == city].copy()

    coordinates = city_df[
        ["lat_rad", "lon_rad"]
    ].to_numpy()

    print("\n" + "-" * 70)
    print(f"City: {city}")
    print(f"Records: {len(city_df):,}")

    for min_samples in MIN_SAMPLES_VALUES:

        for eps_km in EPS_VALUES_KM:

            # Convert kilometres → radians
            eps_radians = eps_km / EARTH_RADIUS_KM

            model = DBSCAN(
                eps=eps_radians,
                min_samples=min_samples,
                metric="haversine",
                algorithm="ball_tree",
                n_jobs=-1
            )

            labels = model.fit_predict(coordinates)

            # ------------------------------------------
            # Cluster statistics
            # ------------------------------------------

            cluster_labels = set(labels)

            if -1 in cluster_labels:
                cluster_labels.remove(-1)

            n_clusters = len(cluster_labels)

            noise_count = np.sum(labels == -1)

            noise_percentage = (
                noise_count / len(labels)
            ) * 100

            clustered_count = len(labels) - noise_count

            clustered_percentage = (
                clustered_count / len(labels)
            ) * 100

            if n_clusters > 0:

                cluster_sizes = pd.Series(labels)

                cluster_sizes = cluster_sizes[
                    cluster_sizes != -1
                ].value_counts()

                largest_cluster = cluster_sizes.max()
                smallest_cluster = cluster_sizes.min()
                median_cluster = cluster_sizes.median()

            else:

                largest_cluster = 0
                smallest_cluster = 0
                median_cluster = 0

            # ------------------------------------------
            # Store result
            # ------------------------------------------

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
                    clustered_percentage, 2
                ),

                "largest_cluster": int(
                    largest_cluster
                ),

                "smallest_cluster": int(
                    smallest_cluster
                ),

                "median_cluster_size": float(
                    median_cluster
                )
            })

            print(
                f"eps={eps_km:>4} km | "
                f"min_samples={min_samples:>2} | "
                f"clusters={n_clusters:>4} | "
                f"noise={noise_percentage:>6.2f}%"
            )


# --------------------------------------------------
# Save results
# --------------------------------------------------

results_df = pd.DataFrame(results)

output_file = os.path.join(
    OUTPUT_DIR,
    "dbscan_parameter_results.csv"
)

results_df.to_csv(
    output_file,
    index=False
)


# --------------------------------------------------
# Display results
# --------------------------------------------------

print("\n" + "=" * 70)
print("PARAMETER ANALYSIS COMPLETED")
print("=" * 70)

print(f"\nTotal parameter combinations tested: {len(results_df):,}")

print(f"\nSaved to:")
print(output_file)


# --------------------------------------------------
# City summaries
# --------------------------------------------------

print("\n" + "=" * 70)
print("RESULT SUMMARY")
print("=" * 70)

for city in sorted(results_df["city"].unique()):

    city_results = results_df[
        results_df["city"] == city
    ]

    print(f"\n{city}")

    print(
        city_results[
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


print("\nDBSCAN parameter testing finished.")