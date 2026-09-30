
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# ROADSAFE INDIA - EXPLORATORY DATA ANALYSIS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "processed" / "indian_accidents_clean.csv"

FIGURES_DIR = BASE_DIR / "outputs" / "figures"
REPORTS_DIR = BASE_DIR / "outputs" / "reports"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")


def save_chart(filename):
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {filename}")


def run_eda():

    print("=" * 65)
    print("ROADSAFE INDIA - EXPLORATORY DATA ANALYSIS")
    print("=" * 65)

    df = pd.read_csv(DATA_FILE, parse_dates=["date"])

    print(f"\nLoaded {len(df):,} accident records.")

    # --------------------------------------------------------
    # 1. ACCIDENTS BY CITY
    # --------------------------------------------------------

    print("\n[1] Accidents by city")

    city_counts = df["city"].value_counts()
    print(city_counts.to_string())

    plt.figure(figsize=(11, 6))

    sns.barplot(
        x=city_counts.values,
        y=city_counts.index,
        color="steelblue"
    )

    plt.title("Recorded Accidents by City")
    plt.xlabel("Number of Accidents")
    plt.ylabel("City")

    save_chart("01_accidents_by_city.png")

    # --------------------------------------------------------
    # 2. ACCIDENT SEVERITY
    # --------------------------------------------------------

    print("\n[2] Accident severity")

    severity_order = ["minor", "major", "fatal"]

    severity_counts = (
        df["accident_severity"]
        .value_counts()
        .reindex(severity_order, fill_value=0)
    )

    print(severity_counts.to_string())

    plt.figure(figsize=(8, 5))

    sns.barplot(
        x=severity_counts.index,
        y=severity_counts.values,
        hue=severity_counts.index,
        palette=["#63A375", "#E5AD45", "#CF5757"],
        legend=False
    )

    plt.title("Accident Severity Distribution")
    plt.xlabel("Severity")
    plt.ylabel("Number of Accidents")

    save_chart("02_accident_severity.png")

    # --------------------------------------------------------
    # 3. ACCIDENT CAUSES
    # --------------------------------------------------------

    print("\n[3] Recorded accident causes")

    cause_counts = df["cause"].value_counts()
    print(cause_counts.to_string())

    plt.figure(figsize=(10, 6))

    sns.barplot(
        x=cause_counts.values,
        y=cause_counts.index,
        color="coral"
    )

    plt.title("Distribution of Recorded Accident Causes")
    plt.xlabel("Number of Accidents")
    plt.ylabel("Recorded Cause")

    save_chart("03_accident_causes.png")

    # --------------------------------------------------------
    # 4. ACCIDENTS BY HOUR
    # --------------------------------------------------------

    print("\n[4] Accidents by hour")

    hourly_counts = (
        df.groupby("hour")
        .size()
        .reindex(range(24), fill_value=0)
    )

    print(hourly_counts.to_string())

    plt.figure(figsize=(12, 5))

    sns.lineplot(
        x=hourly_counts.index,
        y=hourly_counts.values,
        marker="o"
    )

    plt.title("Recorded Accidents by Hour")
    plt.xlabel("Hour of Day")
    plt.ylabel("Number of Accidents")
    plt.xticks(range(24))

    save_chart("04_accidents_by_hour.png")

    # --------------------------------------------------------
    # 5. ROAD TYPE
    # --------------------------------------------------------

    print("\n[5] Accidents by road type")

    road_counts = df["road_type"].value_counts()
    print(road_counts.to_string())

    plt.figure(figsize=(8, 5))

    sns.barplot(
        x=road_counts.index,
        y=road_counts.values,
        color="mediumseagreen"
    )

    plt.title("Recorded Accidents by Road Type")
    plt.xlabel("Road Type")
    plt.ylabel("Number of Accidents")

    save_chart("05_road_type.png")

    # --------------------------------------------------------
    # 6. TRAFFIC DENSITY
    # --------------------------------------------------------

    print("\n[6] Accidents by traffic density")

    density_order = ["low", "medium", "high"]

    density_counts = (
        df["traffic_density"]
        .value_counts()
        .reindex(density_order, fill_value=0)
    )

    print(density_counts.to_string())

    plt.figure(figsize=(8, 5))

    sns.barplot(
        x=density_counts.index,
        y=density_counts.values,
        color="mediumpurple"
    )

    plt.title("Recorded Accidents by Traffic Density")
    plt.xlabel("Traffic Density")
    plt.ylabel("Number of Accidents")

    save_chart("06_traffic_density.png")

    # --------------------------------------------------------
    # 7. CASUALTIES BY CITY
    # --------------------------------------------------------

    print("\n[7] Recorded casualties by city")

    casualties_by_city = (
        df.groupby("city")["casualties"]
        .sum()
        .sort_values(ascending=False)
    )

    print(casualties_by_city.to_string())

    plt.figure(figsize=(11, 6))

    sns.barplot(
        x=casualties_by_city.values,
        y=casualties_by_city.index,
        color="indianred"
    )

    plt.title("Total Recorded Casualties by City")
    plt.xlabel("Total Casualties")
    plt.ylabel("City")

    save_chart("07_casualties_by_city.png")

    # --------------------------------------------------------
    # 8. RISK SCORE DISTRIBUTION
    # --------------------------------------------------------

    print("\n[8] Existing risk score distribution")

    print(df["risk_score"].describe().to_string())

    plt.figure(figsize=(10, 5))

    sns.histplot(
        data=df,
        x="risk_score",
        bins=20,
        color="teal"
    )

    plt.title("Distribution of Dataset Risk Scores")
    plt.xlabel("Risk Score")
    plt.ylabel("Number of Records")

    save_chart("08_risk_score_distribution.png")

    # --------------------------------------------------------
    # 9. YEARLY ACCIDENT COUNTS
    # --------------------------------------------------------

    print("\n[9] Recorded accidents by year")

    df["year"] = df["date"].dt.year

    yearly_counts = df["year"].value_counts().sort_index()

    print(yearly_counts.to_string())

    plt.figure(figsize=(8, 5))

    sns.barplot(
        x=yearly_counts.index,
        y=yearly_counts.values,
        color="slateblue"
    )

    plt.title("Recorded Accidents by Year")
    plt.xlabel("Year")
    plt.ylabel("Number of Accidents")

    save_chart("09_accidents_by_year.png")

    # --------------------------------------------------------
    # 10. SEVERITY BY CITY
    # --------------------------------------------------------

    print("\n[10] Accident severity by city")

    severity_by_city = pd.crosstab(
        df["city"],
        df["accident_severity"]
    ).reindex(columns=severity_order, fill_value=0)

    print(severity_by_city.to_string())

    severity_by_city.plot(
        kind="bar",
        stacked=True,
        figsize=(12, 6),
        color=["#63A375", "#E5AD45", "#CF5757"]
    )

    plt.title("Accident Severity by City")
    plt.xlabel("City")
    plt.ylabel("Number of Accidents")
    plt.xticks(rotation=35, ha="right")
    plt.legend(title="Severity")

    save_chart("10_severity_by_city.png")

    # --------------------------------------------------------
    # 11. SAVE SUMMARY TABLES
    # --------------------------------------------------------

    print("\n[11] Saving summary tables")

    city_counts.rename("accidents").to_csv(
        REPORTS_DIR / "accidents_by_city.csv"
    )

    severity_by_city.to_csv(
        REPORTS_DIR / "severity_by_city.csv"
    )

    casualties_by_city.rename("casualties").to_csv(
        REPORTS_DIR / "casualties_by_city.csv"
    )

    hourly_counts.rename("accidents").to_csv(
        REPORTS_DIR / "accidents_by_hour.csv"
    )

    yearly_counts.rename("accidents").to_csv(
        REPORTS_DIR / "accidents_by_year.csv"
    )

    print("\n" + "=" * 65)
    print("EDA COMPLETE")
    print(f"Charts: {FIGURES_DIR}")
    print(f"Reports: {REPORTS_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    run_eda()
