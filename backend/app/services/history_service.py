from backend.app.utils.data_loader import (
    load_kerala_blackspots,
)


# ============================================================
# HELPERS
# ============================================================

def _safe_float(value):
    """
    Safely convert a value to float.

    Returns None for missing or invalid values.
    """

    if value is None:
        return None

    try:

        if value != value:
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


# ============================================================
# KERALA HISTORICAL BLACK SPOTS
# ============================================================

def get_kerala_history():
    """
    Return historical Kerala black-spot segments with complete
    start and end coordinates for mapping.
    """

    df = load_kerala_blackspots()

    total_records = len(df)

    # A record is mappable as a road segment only when both
    # endpoint coordinate pairs are present.
    mapped = df[
        df["Start Lat"].notna()
        & df["Start Lng"].notna()
        & df["End Lat"].notna()
        & df["End Lng"].notna()
    ].copy()

    records = []

    for _, row in mapped.iterrows():

        records.append(
            {
                "sl_no": row["Sl No"],
                "district": row["Name of District"],
                "police_station": row[
                    "Name of Police Station"
                ],
                "location": row[
                    "Location of Accident Spot"
                ],
                "road_name": row["Name of Road"],
                "road_number": row["Road No"],
                "road_type": row["Type of Road"],
                "road_length": row["Road Length"],
                "start": {
                    "latitude": _safe_float(
                        row["Start Lat"]
                    ),
                    "longitude": _safe_float(
                        row["Start Lng"]
                    ),
                },
                "end": {
                    "latitude": _safe_float(
                        row["End Lat"]
                    ),
                    "longitude": _safe_float(
                        row["End Lng"]
                    ),
                },
            }
        )

    return {
        "dataset": {
            "name": (
                "Kerala Accident "
                "Black Spots 2016"
            ),
            "type": "historical",
            "source_description": (
                "Historical Kerala black-spot "
                "dataset used as a separate "
                "regional reference layer."
            ),
        },
        "summary": {
            "total": int(total_records),
            "mapped": int(len(mapped)),
            "unmapped": int(
                total_records - len(mapped)
            ),
        },
        "records": records,
    }
