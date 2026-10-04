import pandas as pd

from backend.app.utils.data_loader import (
    load_accidents,
    load_clustered_accidents,
)


CATEGORICAL_FACTORS = (
    "road_type",
    "traffic_density",
    "weather",
    "cause",
    "traffic_signal",
    "is_peak_hour",
    "is_weekend",
    "accident_severity",
)


def get_analysis_context(
    city: str | None = None,
    severity: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Build context-scoped summaries directly from source records."""
    records = load_accidents().copy()
    records["date"] = records["date"].astype(str)

    if city and city != "All Cities":
        records = records[records["city"].str.casefold() == city.casefold()]
    if severity and severity != "All Severities":
        records = records[
            records["accident_severity"].str.casefold() == severity.casefold()
        ]
    if start_date:
        records = records[records["date"] >= start_date]
    if end_date:
        records = records[records["date"] <= end_date]

    clustered = load_clustered_accidents()
    clustered["date"] = clustered["date"].astype(str)
    if city and city != "All Cities":
        clustered = clustered[clustered["city"].str.casefold() == city.casefold()]
    if severity and severity != "All Severities":
        clustered = clustered[
            clustered["accident_severity"].str.casefold() == severity.casefold()
        ]
    if start_date:
        clustered = clustered[clustered["date"] >= start_date]
    if end_date:
        clustered = clustered[clustered["date"] <= end_date]
    clustered = clustered[
        (clustered["dbscan_status"] == "clustered")
        & (clustered["dbscan_cluster"] != -1)
    ]
    clustered_counts = clustered.groupby("city").size().to_dict()
    cluster_counts = clustered.groupby("city")["dbscan_cluster"].nunique().to_dict()

    cities = []
    for name, group in records.groupby("city", sort=True):
        cities.append({
            "city": str(name),
            "accidents": int(len(group)),
            "casualties": int(group["casualties"].sum()),
            "fatal_accidents": int((group["accident_severity"] == "fatal").sum()),
            "clustered_records": int(clustered_counts.get(name, 0)),
            "spatial_clusters": int(cluster_counts.get(name, 0)),
        })

    severity_counts = {
        str(name): int(count)
        for name, count in records["accident_severity"].value_counts().items()
    }
    factors = {}
    for column in CATEGORICAL_FACTORS:
        counts = records[column].value_counts(dropna=False)
        denominator = max(len(records), 1)
        factors[column] = [
            {
                "value": "Unknown" if pd.isna(value) else str(value),
                "count": int(count),
                "percent": round(float(count / denominator * 100), 2),
            }
            for value, count in counts.items()
        ]

    yearly = []
    if not records.empty:
        records["year"] = pd.to_datetime(records["date"]).dt.year
        for year, group in records.groupby("year", sort=True):
            yearly.append({
                "year": int(year),
                "accidents": int(len(group)),
                "casualties": int(group["casualties"].sum()),
                "fatal_accidents": int((group["accident_severity"] == "fatal").sum()),
            })

    numeric = {}
    for column in ("casualties", "vehicles_involved", "risk_score"):
        values = records[column].dropna()
        numeric[column] = {
            "count": int(values.count()),
            "mean": round(float(values.mean()), 4) if len(values) else 0,
            "median": round(float(values.median()), 4) if len(values) else 0,
            "min": round(float(values.min()), 4) if len(values) else 0,
            "max": round(float(values.max()), 4) if len(values) else 0,
        }

    return {
        "scope": {
            "city": city or "All Cities",
            "severity": severity or "All Severities",
            "start_date": start_date,
            "end_date": end_date,
        },
        "summary": {
            "accidents": int(len(records)),
            "casualties": int(records["casualties"].sum()),
            "fatal_accidents": int((records["accident_severity"] == "fatal").sum()),
            "clustered_records": int(len(clustered)),
            "spatial_clusters": int(
                len(clustered[["city", "dbscan_cluster"]].drop_duplicates())
            ),
        },
        "cities": cities,
        "severity_counts": severity_counts,
        "factors": factors,
        "numeric": numeric,
        "yearly": yearly,
    }
