import pandas as pd
import os

# =========================
# LOAD EXECUTION DATA
# =========================

df = pd.read_csv(
    "funding_history.csv"
)

# =========================
# CLEAN DATA
# =========================

df["funding_apr"] = pd.to_numeric(
    df["funding_apr"],
    errors="coerce"
)

df = df.dropna()

# =========================
# LOAD REGIME
# =========================

market_regime = "NEUTRAL"

if os.path.exists(
    "market_regime.txt"
):

    with open(
        "market_regime.txt",
        "r"
    ) as f:

        market_regime = (
            f.read().strip()
        )

# =========================
# BASE SIZING
# =========================

def calculate_size(row):

    apr = abs(
        row["funding_apr"]
    )

    size = 1

    # =========================
    # APR FACTOR
    # =========================

    if apr > 50:

        size += 4

    elif apr > 25:

        size += 2

    elif apr > 10:

        size += 1

    # =========================
    # REGIME FACTOR
    # =========================

    if market_regime == "AGGRESSIVE":

        size *= 1.5

    elif market_regime == "DEFENSIVE":

        size *= 0.5

    return round(size, 2)

df["position_size"] = df.apply(
    calculate_size,
    axis=1
)

# =========================
# SORT
# =========================

df = df.sort_values(
    by="position_size",
    ascending=False
)

# =========================
# DISPLAY
# =========================

print("\n")
print("💰 POSITION SIZING")
print("=" * 40)

print(
    f"\nMarket Regime: "
    f"{market_regime}"
)

for _, row in df.head(15).iterrows():

    print("\n")

    print(f"Asset: {row['asset']}")

    print(
        f"Funding APR: "
        f"{round(row['funding_apr'],2)}%"
    )

    print(
        f"Suggested Size: "
        f"{row['position_size']}%"
    )

print("\n")
print("🚀 Position sizing completed")