import pandas as pd
import os

HISTORY_FILE = "funding_history.csv"

# =========================
# LOAD DATA
# =========================

if not os.path.exists(HISTORY_FILE):

    print("No history file found")
    exit()

df = pd.read_csv(HISTORY_FILE)

# =========================
# SCORE ENGINE
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
# RISK ENGINE
# =========================

def classify_risk(row):

    apr = abs(row["apr"])

    persistence = row["persistence"]

    score = row["score"]

    # EXTREME
    if apr > 80 or score > 60:

        return "EXTREME"

    # HIGH
    elif apr > 40 or score > 30:

        return "HIGH"

    # MEDIUM
    elif apr > 20 or score > 15:

        return "MEDIUM"

    # LOW
    else:

        return "LOW"

df["risk"] = df.apply(
    classify_risk,
    axis=1
)

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
print("⚡ RISK ENGINE")
print("==========================")

for _, row in df.iterrows():

    print("\n")

    print(f"Asset: {row['asset']}")

    print(f"APR: {round(row['apr'],2)}%")

    print(f"Persistence: {row['persistence']}")

    print(f"Score: {row['score']}")

    print(f"Risk Level: {row['risk']}")

print("\n")
print("Risk engine completed")