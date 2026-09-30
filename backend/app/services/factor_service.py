from backend.app.utils.data_loader import (
    load_factor_data,
    load_clustered_accidents,
)


# ============================================================
# HELPERS
# ============================================================

def _clean_value(value):
    """
    Convert pandas/numpy values into JSON-friendly values.
    """

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float):
        return round(value, 4)

    return value


def _format_factor_table(df):
    """
    Convert a wide factor CSV into a frontend-friendly structure.

    Example input:

        analysis_group | highway | rural | urban

    Output:

        {
            "analysis_group": "...",
            "values": {
                "highway": 32.65,
                "rural": 35.08,
                "urban": 32.27
            }
        }
    """

    rows = []

    for _, row in df.iterrows():

        analysis_group = str(
            row["analysis_group"]
        )

        values = {}

        for column in df.columns:

            if column == "analysis_group":
                continue

            values[str(column)] = _clean_value(
                row[column]
            )

        rows.append(
            {
                "analysis_group": analysis_group,
                "values": values,
            }
        )

    return rows


# ============================================================
# ALL FACTORS
# ============================================================

def get_factor_summary():
    """
    Return all available categorical factor analyses.
    """

    factor_data = load_factor_data()

    result = {}

    for factor_name, df in factor_data.items():

        result[factor_name] = {
            "columns": [
                str(column)
                for column in df.columns
                if column != "analysis_group"
            ],
            "rows": _format_factor_table(df),
        }

    return result


# ============================================================
# SINGLE FACTOR
# ============================================================

def get_factor(factor_name: str):
    """
    Return one specific factor analysis.
    """

    factor_data = load_factor_data()

    if factor_name not in factor_data:
        return None

    df = factor_data[factor_name]

    return {
        "factor": factor_name,
        "columns": [
            str(column)
            for column in df.columns
            if column != "analysis_group"
        ],
        "rows": _format_factor_table(df),
    }


# ============================================================
# NUMERIC FACTOR SUMMARY
# ============================================================

def get_numeric_factor_summary():
    """
    Calculate numeric summaries directly from clustered
    accident records.

    This intentionally does not rely on the exported
    hotspot_factor_numeric_summary.csv because that file
    contains duplicated pandas column names.
    """

    clustered = load_clustered_accidents()

    # Keep only actual DBSCAN cluster members.
    clustered = clustered[
        (clustered["dbscan_status"] == "clustered")
        & (clustered["dbscan_cluster"] != -1)
    ].copy()

    numeric_columns = [
        "casualties",
        "vehicles_involved",
        "risk_score",
    ]

    summary = {}

    for column in numeric_columns:

        values = clustered[column].dropna()

        summary[column] = {
            "count": int(values.count()),
            "mean": round(
                float(values.mean()),
                4,
            ),
            "median": round(
                float(values.median()),
                4,
            ),
            "min": round(
                float(values.min()),
                4,
            ),
            "max": round(
                float(values.max()),
                4,
            ),
        }

    return {
        "analysis_group": "all_clustered_accidents",
        "records": int(len(clustered)),
        "summary": summary,
    }