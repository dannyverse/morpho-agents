import pandas as pd
import os
from datetime import datetime

# =========================
# LOAD DATA
# =========================

df = pd.read_csv("funding_history.csv")

# =========================
# CLEAN DATA
# =========================

df["funding_apr"] = pd.to_numeric(
    df["funding_apr"],
    errors="coerce"
)

df = df.dropna()

# =========================
# GENERATE SIGNALS
# =========================

signals = []

latest_timestamp = df["timestamp"].max()

latest_df = df[
    df["timestamp"] == latest_timestamp
]

for _, row in latest_df.iterrows():

    asset = row["asset"]

    funding = row["funding_apr"]

    # =========================
    # SHORT CROWDING
    # =========================

    if funding > 25:

        trade = {
            "timestamp": datetime.utcnow(),
            "asset": asset,
            "signal": "SHORT",
            "reason": "Extreme positive funding",
            "funding_apr": funding,
            "status": "OPEN"
        }

        signals.append(trade)

    # =========================
    # LONG SQUEEZE SETUP
    # =========================

    elif funding < -10:

        trade = {
            "timestamp": datetime.utcnow(),
            "asset": asset,
            "signal": "LONG",
            "reason": "Extreme negative funding",
            "funding_apr": funding,
            "status": "OPEN"
        }

        signals.append(trade)

# =========================
# SAVE TRADES
# =========================

if len(signals) == 0:

    print("No paper trade signals")

    exit()

trades_df = pd.DataFrame(signals)

file_name = "paper_trades.csv"

file_exists = os.path.exists(file_name)

file_empty = (
    not file_exists
    or os.path.getsize(file_name) == 0
)

trades_df.to_csv(
    file_name,
    mode="a",
    header=file_empty,
    index=False
)

# =========================
# OUTPUT
# =========================

print("\n🧪 PAPER TRADES\n")

for _, row in trades_df.iterrows():

    print(
        f"{row['signal']} | "
        f"{row['asset']} | "
        f"{round(row['funding_apr'],2)}% | "
        f"{row['reason']}"
    )