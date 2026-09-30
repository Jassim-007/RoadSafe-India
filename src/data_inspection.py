import pandas as pd
from pathlib import Path


# ============================================================
# ROADSAFE INDIA - DATA INSPECTION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

INDIA_FILE = DATA_DIR / "indian_roads_dataset (1).xlsx"


def inspect_indian_dataset():
    print("=" * 70)
    print("ROADSAFE INDIA - INDIAN ACCIDENT DATASET INSPECTION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load Excel file
    # --------------------------------------------------------
    print("\n[1] Loading dataset...")

    df = pd.read_excel(INDIA_FILE)

    print(f"File: {INDIA_FILE.name}")
    print(f"Rows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]:,}")

    # --------------------------------------------------------
    # Column names
    # --------------------------------------------------------
    print("\n[2] COLUMN NAMES")
    print("-" * 70)

    for i, column in enumerate(df.columns, start=1):
        print(f"{i:2}. {column}")

    # --------------------------------------------------------
    # Data types
    # --------------------------------------------------------
    print("\n[3] DATA TYPES")
    print("-" * 70)

    print(df.dtypes.to_string())

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------
    print("\n[4] MISSING VALUES")
    print("-" * 70)

    missing = df.isnull().sum()
    missing_percent = (missing / len(df)) * 100

    missing_report = pd.DataFrame({
        "Missing": missing,
        "Percentage": missing_percent.round(2)
    })

    print(missing_report[missing_report["Missing"] > 0].to_string())

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------
    print("\n[5] DUPLICATE ROWS")
    print("-" * 70)

    duplicate_count = df.duplicated().sum()

    print(f"Duplicate rows: {duplicate_count:,}")

    # --------------------------------------------------------
    # Coordinate validation
    # --------------------------------------------------------
    print("\n[6] COORDINATE VALIDATION")
    print("-" * 70)

    if "latitude" in df.columns and "longitude" in df.columns:

        invalid_lat = (
            df["latitude"].isna()
            | ~df["latitude"].between(-90, 90)
        ).sum()

        invalid_lon = (
            df["longitude"].isna()
            | ~df["longitude"].between(-180, 180)
        ).sum()

        print(f"Invalid/missing latitude:  {invalid_lat:,}")
        print(f"Invalid/missing longitude: {invalid_lon:,}")

        valid_coordinates = (
            df["latitude"].between(-90, 90)
            & df["longitude"].between(-180, 180)
        ).sum()

        print(f"Valid coordinate pairs:    {valid_coordinates:,}")

    # --------------------------------------------------------
    # Cities
    # --------------------------------------------------------
    print("\n[7] CITIES")
    print("-" * 70)

    if "city" in df.columns:
        print(f"Unique cities: {df['city'].nunique()}")

        print("\nAccidents by city:")
        print(df["city"].value_counts().to_string())

    # --------------------------------------------------------
    # States
    # --------------------------------------------------------
    print("\n[8] STATES")
    print("-" * 70)

    if "state" in df.columns:
        print(f"Unique states: {df['state'].nunique()}")

        print("\nAccidents by state:")
        print(df["state"].value_counts().to_string())

    # --------------------------------------------------------
    # Accident severity
    # --------------------------------------------------------
    print("\n[9] ACCIDENT SEVERITY")
    print("-" * 70)

    if "accident_severity" in df.columns:
        print(df["accident_severity"].value_counts(dropna=False).to_string())

    # --------------------------------------------------------
    # Date information
    # --------------------------------------------------------
    print("\n[10] DATE INFORMATION")
    print("-" * 70)

    if "date" in df.columns:

        date_column = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        print(f"Invalid dates: {date_column.isna().sum():,}")

        valid_dates = date_column.dropna()

        if len(valid_dates) > 0:
            print(f"Earliest date: {valid_dates.min()}")
            print(f"Latest date:   {valid_dates.max()}")

    # --------------------------------------------------------
    # Important categorical variables
    # --------------------------------------------------------
    categorical_columns = [
        "road_type",
        "traffic_signal",
        "weather",
        "traffic_density",
        "cause",
        "day_of_week",
        "is_weekend",
        "is_peak_hour",
        "festival",
    ]

    print("\n[11] CATEGORICAL VARIABLES")
    print("-" * 70)

    for column in categorical_columns:

        if column in df.columns:

            print(f"\n--- {column} ---")
            print(df[column].value_counts(dropna=False).to_string())

    # --------------------------------------------------------
    # Numeric summary
    # --------------------------------------------------------
    print("\n[12] NUMERIC SUMMARY")
    print("-" * 70)

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    print(
        df[numeric_columns]
        .describe()
        .transpose()
        .to_string()
    )

    # --------------------------------------------------------
    # Sample records
    # --------------------------------------------------------
    print("\n[13] SAMPLE RECORDS")
    print("-" * 70)

    print(df.head(5).to_string())

    print("\n" + "=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    inspect_indian_dataset()