import pandas as pd
from pathlib import Path


# ============================================================
# ROADSAFE INDIA - DATA CLEANING
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "data" / "raw" / "indian_roads_dataset (1).xlsx"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = PROCESSED_DIR / "indian_accidents_clean.csv"


def clean_indian_dataset():

    print("=" * 70)
    print("ROADSAFE INDIA - DATA CLEANING")
    print("=" * 70)

    # --------------------------------------------------------
    # Create processed directory
    # --------------------------------------------------------

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Load raw dataset
    # --------------------------------------------------------

    print("\n[1] Loading raw dataset...")

    df = pd.read_excel(RAW_FILE)

    print(f"Original rows: {len(df):,}")
    print(f"Original columns: {len(df.columns)}")

    # --------------------------------------------------------
    # Remove accidental whitespace from column names
    # --------------------------------------------------------

    df.columns = df.columns.str.strip()

    # --------------------------------------------------------
    # Clean string columns
    # --------------------------------------------------------

    print("\n[2] Cleaning text fields...")

    string_columns = df.select_dtypes(include=["object", "str"]).columns

    for column in string_columns:
        df[column] = df[column].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )

    # --------------------------------------------------------
    # Convert date column
    # --------------------------------------------------------

    print("\n[3] Validating dates...")

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    invalid_dates = df["date"].isna().sum()

    print(f"Invalid dates: {invalid_dates:,}")

    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    print("\n[4] Validating coordinates...")

    valid_coordinates = (
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
    )

    invalid_coordinates = (~valid_coordinates).sum()

    print(f"Invalid coordinate records: {invalid_coordinates:,}")

    # Remove only genuinely invalid coordinates
    df = df[valid_coordinates].copy()

    # --------------------------------------------------------
    # Check duplicate accident IDs
    # --------------------------------------------------------

    print("\n[5] Checking accident IDs...")

    duplicate_ids = df["accident_id"].duplicated().sum()

    print(f"Duplicate accident IDs: {duplicate_ids:,}")

    # We do NOT automatically remove them.
    # The inspection showed the IDs are unique.
    
    # --------------------------------------------------------
    # Validate numerical fields
    # --------------------------------------------------------

    print("\n[6] Validating numerical fields...")

    numerical_ranges = {
        "hour": (0, 23),
        "lanes": (1, None),
        "vehicles_involved": (1, None),
        "casualties": (0, None),
        "temperature": (None, None),
        "risk_score": (0, 1),
    }

    for column, (minimum, maximum) in numerical_ranges.items():

        if column not in df.columns:
            continue

        if minimum is not None:
            invalid_min = (df[column] < minimum).sum()
        else:
            invalid_min = 0

        if maximum is not None:
            invalid_max = (df[column] > maximum).sum()
        else:
            invalid_max = 0

        print(
            f"{column}: "
            f"{invalid_min + invalid_max:,} invalid values"
        )

    # --------------------------------------------------------
    # Preserve missing festival values
    # --------------------------------------------------------

    print("\n[7] Festival field")

    festival_missing = df["festival"].isna().sum()

    print(
        f"Missing festival values: "
        f"{festival_missing:,}"
    )

    print(
        "Festival missing values are being preserved "
        "for later analysis."
    )

    # --------------------------------------------------------
    # Sort by date
    # --------------------------------------------------------

    print("\n[8] Sorting dataset...")

    df = df.sort_values(
        by=["date", "accident_id"]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Save cleaned dataset
    # --------------------------------------------------------

    print("\n[9] Saving cleaned dataset...")

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"Saved to: {OUTPUT_FILE}")
    print(f"Final rows: {len(df):,}")
    print(f"Final columns: {len(df.columns)}")

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    print("\n[10] FINAL CHECK")
    print("-" * 70)

    print(
        f"Missing values: "
        f"{df.isna().sum().sum():,}"
    )

    print(
        f"Duplicate rows: "
        f"{df.duplicated().sum():,}"
    )

    print(
        f"Latitude range: "
        f"{df['latitude'].min():.6f} → "
        f"{df['latitude'].max():.6f}"
    )

    print(
        f"Longitude range: "
        f"{df['longitude'].min():.6f} → "
        f"{df['longitude'].max():.6f}"
    )

    print("\n" + "=" * 70)
    print("CLEANING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    clean_indian_dataset()