import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors

# --------------------------------------------------
# Paths
# --------------------------------------------------

INPUT_FILE = "data/processed/indian_accidents_clean.csv"
OUTPUT_DIR = "outputs/clusters"
FIGURE_DIR = "outputs/figures"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)


# --------------------------------------------------
# Haversine distance
# --------------------------------------------------

def haversine_distance_matrix(points):
    """
    Calculate pairwise Haversine distance between
    latitude/longitude coordinates.

    Returns distance in kilometres.
    """

    R = 6371.0088

    lat = np.radians(points[:, 0])
    lon = np.radians(points[:, 1])

    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat[:, None])
        * np.cos(lat[None, :])
        * np.sin(dlon / 2) ** 2
    )

    return R * 2 * np.arcsin(np.sqrt(a))


# --------------------------------------------------
# Load data
# --------------------------------------------------

print("=" * 60)
print("ROADSAFE INDIA - SPATIAL PREPARATION")
print("=" * 60)

df = pd.read_csv(INPUT_FILE)

print(f"\nTotal records: {len(df):,}")
print(f"Cities: {df['city'].nunique()}")

print("\nAccidents by city:")
print(df["city"].value_counts())


# --------------------------------------------------
# City-wise k-distance analysis
# --------------------------------------------------

K = 10

summary = []

for city in sorted(df["city"].unique()):

    city_df = df[df["city"] == city].copy()

    coordinates = city_df[["latitude", "longitude"]].to_numpy()

    print("\n" + "-" * 60)
    print(f"City: {city}")
    print(f"Records: {len(city_df):,}")

    # Convert lat/lon to radians for Haversine metric
    coordinates_rad = np.radians(coordinates)

    neighbors = NearestNeighbors(
        n_neighbors=K,
        metric="haversine",
        algorithm="ball_tree"
    )

    neighbors.fit(coordinates_rad)

    distances, indices = neighbors.kneighbors(coordinates_rad)

    # K-th nearest-neighbour distance
    kth_distances = distances[:, K - 1]

    # Convert radians to kilometres
    kth_distances_km = kth_distances * 6371.0088

    kth_distances_km = np.sort(kth_distances_km)

    # Save distances
    distance_file = os.path.join(
        OUTPUT_DIR,
        f"{city.lower()}_k_distance.csv"
    )

    pd.DataFrame({
        "k_distance_km": kth_distances_km
    }).to_csv(distance_file, index=False)

    # Plot
    plt.figure(figsize=(10, 6))

    plt.plot(
        range(1, len(kth_distances_km) + 1),
        kth_distances_km
    )

    plt.xlabel("Points sorted by distance")
    plt.ylabel(f"{K}-Nearest Neighbor Distance (km)")
    plt.title(f"{city} - {K}-Distance Plot")

    plt.grid(True, alpha=0.3)

    plot_file = os.path.join(
        FIGURE_DIR,
        f"{city.lower()}_k_distance.png"
    )

    plt.tight_layout()
    plt.savefig(plot_file, dpi=300)
    plt.close()

    # Percentiles for parameter selection
    percentiles = {
        "city": city,
        "records": len(city_df),
        "p50_km": np.percentile(kth_distances_km, 50),
        "p75_km": np.percentile(kth_distances_km, 75),
        "p90_km": np.percentile(kth_distances_km, 90),
        "p95_km": np.percentile(kth_distances_km, 95),
        "p99_km": np.percentile(kth_distances_km, 99),
        "max_km": kth_distances_km.max()
    }

    summary.append(percentiles)


# --------------------------------------------------
# Save summary
# --------------------------------------------------

summary_df = pd.DataFrame(summary)

summary_file = os.path.join(
    OUTPUT_DIR,
    "k_distance_summary.csv"
)

summary_df.to_csv(summary_file, index=False)

print("\n" + "=" * 60)
print("K-DISTANCE SUMMARY")
print("=" * 60)

print(summary_df.to_string(index=False))

print("\nSaved:")
print(f"  {summary_file}")
print(f"  {FIGURE_DIR}")
print(f"  {OUTPUT_DIR}")

print("\nSpatial preparation completed successfully.")