"""
RoadSafe India
Interactive Hotspot Mapping

Layers:
1. Esri World Street Map
2. Multiple-indicator DBSCAN hotspots
3. DBSCAN cluster centroids
4. Accident locations
5. Kerala historical black spots
6. Individual city accident layers

Important:
    Kerala historical black spots are kept as a separate
    dataset and are NOT merged with the contemporary
    Indian accident dataset.
"""

from pathlib import Path

import pandas as pd
import folium
from folium.plugins import MarkerCluster


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

KERALA_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "Kerala_Accident_Black_Spots_2016.xlsx"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "maps"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "roadsafe_india_hotspot_map.html"
)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("ROADSAFE INDIA - INTERACTIVE HOTSPOT MAPPING")
print("=" * 70)


# ============================================================
# LOAD ACCIDENT DATA
# ============================================================

print("\nLoading accident data...")

df = pd.read_csv(
    ACCIDENT_FILE
)

print(
    f"Accident records loaded: "
    f"{len(df):,}"
)


# ============================================================
# LOAD HOTSPOT RISK DATA
# ============================================================

print("\nLoading hotspot-risk data...")

risk = pd.read_csv(
    RISK_FILE
)

print(
    f"Hotspot candidates loaded: "
    f"{len(risk):,}"
)


# ============================================================
# CHECK REQUIRED ACCIDENT COLUMNS
# ============================================================

required_accident_columns = [
    "accident_id",
    "city",
    "latitude",
    "longitude",
    "dbscan_cluster",
    "dbscan_status",
    "accident_severity",
    "casualties",
    "risk_score",
    "road_type",
    "weather",
    "cause",
]

missing_columns = [
    column
    for column in required_accident_columns
    if column not in df.columns
]

if missing_columns:

    raise ValueError(
        "Missing required accident columns: "
        f"{missing_columns}"
    )


# ============================================================
# CHECK REQUIRED RISK COLUMNS
# ============================================================

required_risk_columns = [
    "city",
    "dbscan_cluster",
    "risk_profile",
    "accident_count",
    "fatality_proportion",
    "total_casualties",
    "mean_risk_score",
    "mean_vehicles",
    "accident_count_percentile",
    "fatality_proportion_percentile",
    "total_casualties_percentile",
    "mean_risk_score_percentile",
]

missing_risk_columns = [
    column
    for column in required_risk_columns
    if column not in risk.columns
]

if missing_risk_columns:

    raise ValueError(
        "Missing required risk columns: "
        f"{missing_risk_columns}"
    )


# ============================================================
# VALID ACCIDENT COORDINATES
# ============================================================

df = df.dropna(
    subset=[
        "latitude",
        "longitude"
    ]
).copy()

print(
    f"Records with valid coordinates: "
    f"{len(df):,}"
)


# ============================================================
# IDENTIFY MULTIPLE-INDICATOR HOTSPOTS
# ============================================================

hotspot_risk = risk[
    risk["risk_profile"]
    == "multiple_high_risk_indicators"
].copy()

hotspot_keys = set(
    zip(
        hotspot_risk["city"],
        hotspot_risk["dbscan_cluster"]
    )
)

print(
    f"Multiple-indicator hotspots: "
    f"{len(hotspot_risk):,}"
)


# ============================================================
# MAP CENTER
# ============================================================

map_center = [
    df["latitude"].mean(),
    df["longitude"].mean()
]

print(
    f"\nMap center: "
    f"{map_center[0]:.4f}, "
    f"{map_center[1]:.4f}"
)


# ============================================================
# CREATE MAP
# ============================================================

print(
    "\nCreating map..."
)

m = folium.Map(
    location=map_center,
    zoom_start=5,
    tiles=None,
    control_scale=True
)


# ============================================================
# ESRI WORLD STREET MAP
# ============================================================

folium.TileLayer(
    tiles=(
        "https://server.arcgisonline.com/"
        "ArcGIS/rest/services/"
        "World_Street_Map/"
        "MapServer/tile/{z}/{y}/{x}"
    ),
    attr=(
        "Esri, HERE, Garmin, Intermap, "
        "increment P Corp., GEBCO, USGS, FAO, "
        "NPS"
    ),
    name="Esri World Street Map",
    overlay=False,
    control=True,
    show=True
).add_to(m)


# ============================================================
# ACCIDENT LOCATION LAYER
# ============================================================

print(
    "\nAdding accident location layer..."
)

accident_layer = folium.FeatureGroup(
    name="Accident Locations",
    show=False
)

marker_cluster = MarkerCluster(
    name="Accident Records"
)


for _, row in df.iterrows():

    popup_html = f"""
    <div style="width:280px">

    <h4>Accident Record</h4>

    <b>City:</b>
        {row['city']}<br>

    <b>Accident ID:</b>
        {row['accident_id']}<br>

    <b>Severity:</b>
        {row['accident_severity']}<br>

    <b>Casualties:</b>
        {row['casualties']}<br>

    <b>Risk Score:</b>
        {row['risk_score']:.3f}<br>

    <b>Road Type:</b>
        {row['road_type']}<br>

    <b>Weather:</b>
        {row['weather']}<br>

    <b>Cause:</b>
        {row['cause']}<br>

    <b>DBSCAN Cluster:</b>
        {row['dbscan_cluster']}

    </div>
    """

    marker = folium.CircleMarker(
        location=[
            row["latitude"],
            row["longitude"]
        ],
        radius=2,
        weight=0,
        fill=True,
        fill_opacity=0.45,
        popup=folium.Popup(
            popup_html,
            max_width=300
        )
    )

    marker_cluster.add_child(
        marker
    )


accident_layer.add_child(
    marker_cluster
)

accident_layer.add_to(m)


# ============================================================
# MULTIPLE-INDICATOR HOTSPOT LAYER
# ============================================================

print(
    "Adding multiple-indicator hotspots..."
)

hotspot_layer = folium.FeatureGroup(
    name="Multiple-Indicator Hotspots",
    show=True
)


for _, hotspot in hotspot_risk.iterrows():

    city = hotspot["city"]

    cluster_id = int(
        hotspot["dbscan_cluster"]
    )

    cluster_points = df[
        (df["city"] == city)
        &
        (
            df["dbscan_cluster"]
            == cluster_id
        )
    ].copy()

    if cluster_points.empty:
        continue


    # --------------------------------------------------------
    # HOTSPOT CENTROID
    # --------------------------------------------------------

    centroid_lat = (
        cluster_points["latitude"]
        .mean()
    )

    centroid_lon = (
        cluster_points["longitude"]
        .mean()
    )


    # --------------------------------------------------------
    # HOTSPOT POPUP
    # --------------------------------------------------------

    popup_html = f"""
    <div style="width:330px">

    <h3>Multiple-Indicator Hotspot</h3>

    <b>City:</b>
        {city}<br>

    <b>DBSCAN Cluster:</b>
        {cluster_id}<br>

    <b>Accidents:</b>
        {int(hotspot['accident_count'])}<br>

    <b>Fatality Proportion:</b>
        {hotspot['fatality_proportion'] * 100:.2f}%<br>

    <b>Total Casualties:</b>
        {int(hotspot['total_casualties'])}<br>

    <b>Mean Risk Score:</b>
        {hotspot['mean_risk_score']:.3f}<br>

    <b>Mean Vehicles Involved:</b>
        {hotspot['mean_vehicles']:.2f}

    <hr>

    <h4>City-Relative Indicators</h4>

    <b>Accident Concentration:</b>
        {hotspot['accident_count_percentile'] * 100:.1f}
        percentile<br>

    <b>Fatality Proportion:</b>
        {hotspot['fatality_proportion_percentile'] * 100:.1f}
        percentile<br>

    <b>Casualty Burden:</b>
        {hotspot['total_casualties_percentile'] * 100:.1f}
        percentile<br>

    <b>Mean Risk Score:</b>
        {hotspot['mean_risk_score_percentile'] * 100:.1f}
        percentile

    </div>
    """


    # --------------------------------------------------------
    # HOTSPOT MARKER
    # --------------------------------------------------------

    folium.Marker(
        location=[
            centroid_lat,
            centroid_lon
        ],
        popup=folium.Popup(
            popup_html,
            max_width=360
        ),
        tooltip=(
            f"{city} | "
            f"Cluster {cluster_id} | "
            f"{int(hotspot['accident_count'])} accidents"
        ),
        icon=folium.Icon(
            icon="exclamation-triangle",
            prefix="fa"
        )
    ).add_to(
        hotspot_layer
    )


    # --------------------------------------------------------
    # APPROXIMATE VISUAL BOUNDARY
    # --------------------------------------------------------
    #
    # This rectangle is ONLY a visualization aid.
    # It is NOT the actual statistical DBSCAN boundary.
    #

    min_lat = (
        cluster_points["latitude"]
        .min()
    )

    max_lat = (
        cluster_points["latitude"]
        .max()
    )

    min_lon = (
        cluster_points["longitude"]
        .min()
    )

    max_lon = (
        cluster_points["longitude"]
        .max()
    )

    bounds = [
        [min_lat, min_lon],
        [min_lat, max_lon],
        [max_lat, max_lon],
        [max_lat, min_lon],
        [min_lat, min_lon],
    ]

    folium.PolyLine(
        locations=bounds,
        weight=2,
        opacity=0.8,
        tooltip=(
            f"{city} - "
            f"Hotspot Cluster {cluster_id}"
        )
    ).add_to(
        hotspot_layer
    )


hotspot_layer.add_to(m)


# ============================================================
# ALL DBSCAN CLUSTER CENTROIDS
# ============================================================

print(
    "Adding DBSCAN cluster centroids..."
)

cluster_layer = folium.FeatureGroup(
    name="DBSCAN Cluster Centroids",
    show=False
)

clustered = df[
    (df["dbscan_cluster"] != -1)
    &
    (df["dbscan_status"] != "excluded")
].copy()


cluster_centroids = (
    clustered
    .groupby(
        [
            "city",
            "dbscan_cluster"
        ]
    )
    .agg(
        latitude=(
            "latitude",
            "mean"
        ),
        longitude=(
            "longitude",
            "mean"
        ),
        accidents=(
            "dbscan_cluster",
            "size"
        )
    )
    .reset_index()
)


for _, row in cluster_centroids.iterrows():

    popup_html = f"""
    <div style="width:240px">

    <h4>DBSCAN Cluster</h4>

    <b>City:</b>
        {row['city']}<br>

    <b>Cluster:</b>
        {int(row['dbscan_cluster'])}<br>

    <b>Accidents:</b>
        {int(row['accidents'])}

    </div>
    """

    folium.CircleMarker(
        location=[
            row["latitude"],
            row["longitude"]
        ],
        radius=4,
        weight=1,
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(
            popup_html,
            max_width=250
        ),
        tooltip=(
            f"{row['city']} | "
            f"Cluster "
            f"{int(row['dbscan_cluster'])}"
        )
    ).add_to(
        cluster_layer
    )


cluster_layer.add_to(m)


# ============================================================
# KERALA HISTORICAL BLACK-SPOT LAYER
# ============================================================

print(
    "\nLoading Kerala black-spot dataset..."
)

kerala = pd.read_excel(
    KERALA_FILE
)

print(
    f"Kerala records loaded: "
    f"{len(kerala):,}"
)


# ============================================================
# EXACT KERALA COLUMNS
# ============================================================

KERALA_LAT = "Start Lat"
KERALA_LNG = "Start Lng"

required_kerala_columns = [
    "Name of District",
    "Name of Police Station",
    "Location of Accident Spot",
    "Name of Road",
    "Road No",
    "Type of Road",
    "Start Lat",
    "Start Lng",
]

missing_kerala = [
    column
    for column in required_kerala_columns
    if column not in kerala.columns
]

if missing_kerala:

    print(
        "\nWARNING:"
        " Missing Kerala columns:"
    )

    print(
        missing_kerala
    )

else:

    kerala_layer = folium.FeatureGroup(
        name="Kerala Historical Black Spots",
        show=False
    )

    # --------------------------------------------------------
    # CONVERT COORDINATES
    # --------------------------------------------------------

    kerala[KERALA_LAT] = pd.to_numeric(
        kerala[KERALA_LAT],
        errors="coerce"
    )

    kerala[KERALA_LNG] = pd.to_numeric(
        kerala[KERALA_LNG],
        errors="coerce"
    )

    kerala_valid = kerala.dropna(
        subset=[
            KERALA_LAT,
            KERALA_LNG
        ]
    ).copy()

    print(
        f"Kerala records with valid "
        f"start coordinates: "
        f"{len(kerala_valid):,}"
    )


    # --------------------------------------------------------
    # ADD KERALA MARKERS
    # --------------------------------------------------------

    for _, row in kerala_valid.iterrows():

        popup_parts = []

        fields = [
            "Name of District",
            "Name of Police Station",
            "Location of Accident Spot",
            "Name of Road",
            "Road No",
            "Type of Road",
        ]

        for field in fields:

            value = row[field]

            if pd.notna(value):

                popup_parts.append(
                    f"<b>{field}:</b> "
                    f"{value}"
                )

        popup_html = (
            "<div style='width:330px'>"
            "<h3>Kerala Historical Black Spot</h3>"
            + "<br>".join(popup_parts)
            + "</div>"
        )

        folium.CircleMarker(
            location=[
                row[KERALA_LAT],
                row[KERALA_LNG]
            ],
            radius=6,
            weight=1,
            fill=True,
            fill_opacity=0.85,
            popup=folium.Popup(
                popup_html,
                max_width=350
            ),
            tooltip=(
                "Kerala Historical "
                "Black Spot"
            )
        ).add_to(
            kerala_layer
        )


    kerala_layer.add_to(m)


# ============================================================
# CITY ACCIDENT LAYERS
# ============================================================

print(
    "\nCreating city layers..."
)

cities = sorted(
    df[
        df["dbscan_status"]
        != "excluded"
    ]["city"]
    .dropna()
    .unique()
)


for city in cities:

    city_layer = folium.FeatureGroup(
        name=f"{city} Accident Records",
        show=False
    )

    city_data = df[
        df["city"] == city
    ].copy()

    # Only actual DBSCAN clustered records
    city_data = city_data[
        city_data["dbscan_cluster"] != -1
    ]

    for _, row in city_data.iterrows():

        popup_html = f"""
        <div style="width:240px">

        <b>City:</b>
            {city}<br>

        <b>Severity:</b>
            {row['accident_severity']}<br>

        <b>Cluster:</b>
            {int(row['dbscan_cluster'])}<br>

        <b>Risk Score:</b>
            {row['risk_score']:.3f}

        </div>
        """

        folium.CircleMarker(
            location=[
                row["latitude"],
                row["longitude"]
            ],
            radius=2,
            weight=0,
            fill=True,
            fill_opacity=0.35,
            popup=folium.Popup(
                popup_html,
                max_width=250
            )
        ).add_to(
            city_layer
        )

    city_layer.add_to(m)


# ============================================================
# LAYER CONTROL
# ============================================================

folium.LayerControl(
    collapsed=False
).add_to(m)


# ============================================================
# SAVE MAP
# ============================================================

print(
    "\nSaving interactive map..."
)

m.save(
    OUTPUT_FILE
)

print(
    "\nMap saved successfully:"
)

print(
    OUTPUT_FILE
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("MAPPING COMPLETED")
print("=" * 70)

print(
    "\nLayers included:"
)

print(
    "1. Esri World Street Map"
)

print(
    "2. Multiple-Indicator Hotspots"
)

print(
    "3. DBSCAN Cluster Centroids"
)

print(
    "4. Accident Locations"
)

print(
    "5. Kerala Historical Black Spots"
)

print(
    "6. Individual City Accident Layers"
)

print("=" * 70)