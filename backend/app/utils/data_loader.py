from pathlib import Path

import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CLUSTERS_DIR = PROJECT_ROOT / "outputs" / "clusters"
RAW_DIR = PROJECT_ROOT / "data" / "raw"


# ============================================================
# MAIN DATA FILES
# ============================================================

ACCIDENTS_FILE = (
    PROCESSED_DIR / "indian_accidents_clean.csv"
)

CLUSTERED_ACCIDENTS_FILE = (
    CLUSTERS_DIR / "final_clustered_accidents.csv"
)

CLUSTER_SUMMARY_FILE = (
    CLUSTERS_DIR / "cluster_summary.csv"
)

CLUSTER_CITY_SUMMARY_FILE = (
    CLUSTERS_DIR / "cluster_city_summary.csv"
)

HOTSPOT_CANDIDATES_FILE = (
    CLUSTERS_DIR / "hotspot_candidates.csv"
)

HOTSPOT_RISK_FILE = (
    CLUSTERS_DIR / "hotspot_risk_candidates.csv"
)

HOTSPOT_RISK_CITY_FILE = (
    CLUSTERS_DIR / "hotspot_risk_city_summary.csv"
)

HOTSPOT_FACTOR_CITY_FILE = (
    CLUSTERS_DIR / "hotspot_factor_city_summary.csv"
)


# ============================================================
# KERALA HISTORICAL DATA
# ============================================================

KERALA_BLACKSPOTS_FILE = (
    RAW_DIR / "Kerala_Accident_Black_Spots_2016.xlsx"
)


# ============================================================
# FACTOR ANALYSIS FILES
# ============================================================

FACTOR_DIR = CLUSTERS_DIR

FACTOR_FILES = {
    "road_type": (
        FACTOR_DIR / "hotspot_factor_road_type.csv"
    ),
    "traffic_density": (
        FACTOR_DIR / "hotspot_factor_traffic_density.csv"
    ),
    "weather": (
        FACTOR_DIR / "hotspot_factor_weather.csv"
    ),
    "cause": (
        FACTOR_DIR / "hotspot_factor_cause.csv"
    ),
    "traffic_signal": (
        FACTOR_DIR / "hotspot_factor_traffic_signal.csv"
    ),
    "peak_hour": (
        FACTOR_DIR / "hotspot_factor_is_peak_hour.csv"
    ),
    "weekend": (
        FACTOR_DIR / "hotspot_factor_is_weekend.csv"
    ),
    "accident_severity": (
        FACTOR_DIR / "hotspot_factor_accident_severity.csv"
    ),
}


# ============================================================
# GENERIC CSV LOADER
# ============================================================

def load_csv(path: Path) -> pd.DataFrame:
    """
    Load a CSV file and raise a clear error if it does not exist.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}"
        )

    return pd.read_csv(path)


# ============================================================
# ACCIDENT DATA LOADERS
# ============================================================

def load_accidents() -> pd.DataFrame:
    """
    Load the cleaned Indian accident dataset.
    """

    return load_csv(ACCIDENTS_FILE)


def load_clustered_accidents() -> pd.DataFrame:
    """
    Load the final DBSCAN clustered accident dataset.
    """

    return load_csv(CLUSTERED_ACCIDENTS_FILE)


# ============================================================
# CLUSTER DATA LOADERS
# ============================================================

def load_cluster_summary() -> pd.DataFrame:
    """
    Load cluster-level summary data.
    """

    return load_csv(CLUSTER_SUMMARY_FILE)


def load_cluster_city_summary() -> pd.DataFrame:
    """
    Load city-level DBSCAN cluster summary.
    """

    return load_csv(CLUSTER_CITY_SUMMARY_FILE)


# ============================================================
# HOTSPOT DATA LOADERS
# ============================================================

def load_hotspot_candidates() -> pd.DataFrame:
    """
    Load hotspot candidate analysis.
    """

    return load_csv(HOTSPOT_CANDIDATES_FILE)


def load_hotspot_risk() -> pd.DataFrame:
    """
    Load hotspot risk analysis.
    """

    return load_csv(HOTSPOT_RISK_FILE)


def load_hotspot_risk_city() -> pd.DataFrame:
    """
    Load city-level hotspot risk summary.
    """

    return load_csv(HOTSPOT_RISK_CITY_FILE)


def load_hotspot_factor_city() -> pd.DataFrame:
    """
    Load city-level hotspot factor summary.
    """

    return load_csv(HOTSPOT_FACTOR_CITY_FILE)


# ============================================================
# FACTOR DATA LOADER
# ============================================================

def load_factor_data() -> dict[str, pd.DataFrame]:
    """
    Load all categorical hotspot factor analysis files.

    Returns:
        Dictionary mapping factor names to pandas DataFrames.
    """

    return {
        name: load_csv(path)
        for name, path in FACTOR_FILES.items()
    }


# ============================================================
# KERALA HISTORICAL DATA LOADER
# ============================================================

def load_kerala_blackspots() -> pd.DataFrame:
    """
    Load the historical Kerala accident black-spot dataset.
    """

    if not KERALA_BLACKSPOTS_FILE.exists():
        raise FileNotFoundError(
            f"Kerala black-spot file not found: "
            f"{KERALA_BLACKSPOTS_FILE}"
        )

    return pd.read_excel(KERALA_BLACKSPOTS_FILE)