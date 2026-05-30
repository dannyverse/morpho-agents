import pandas as pd
import os

HISTORY_FILE = "funding_history.csv"

CAPITAL = 1000

# =========================
# LOAD DATA
# =========================

if not os.path.exists(HISTORY_FILE):

    print("No history file found")
    exit()

df = pd.read_csv(HISTORY_FILE)

# =========================
# ESTIMATE FUNDING
# =========================

def estimate_daily_funding(apr):

    yearly = CAPITAL * (apr / 100)

    daily = yearly / 365

    return round(daily, 2)

# =========================
# SCORE
# =========================

def calculate_score(row):

    score = 0

    score += abs(row["apr"]) * 0.25

    score += row["persistence"] * 15

    return round(score, 2)

df["score"] = df.apply(
    calculate_score,
    axis=1
)

# =========================
# ESTIMATES
# =========================

df["daily_estimate"] = df["apr"].apply(
    estimate_daily_funding
)

df["monthly_estimate"] = (
    df["daily_estimate"] * 30
).round(2)

# =========================
# SORT
# =========================

df = df.sort_values(
    by="score",
    ascending=False
)

# =========================
# DISPLAY
# =========================

print("\n")
print("⚡ TRADE SIMULATION")
print("==========================")

for _, row in df.iterrows():

    print("\n")

    print(f"Asset: {row['asset']}")

    print(f"APR: {round(row['apr'],2)}%")

    print(f"Persistence: {row['persistence']}")

    print(f"Score: {row['score']}")

    print(f"Estimated Daily Funding: ${row['daily_estimate']}")

    print(f"Estimated Monthly Funding: ${row['monthly_estimate']}")

print("\n")
print("Trade simulator completed")