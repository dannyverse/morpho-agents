import pandas as pd
import sqlite3
from datetime import datetime

# =========================
# LOAD FUNDING HISTORY
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
# BUILD SIGNALS
# =========================

signals = []

timestamp = datetime.utcnow()

for asset in df["asset"].unique():

    asset_df = df[
        df["asset"] == asset
    ]

    avg_funding = round(
        asset_df["funding_apr"].mean(),
        2
    )

    persistence = len(

        asset_df[
            abs(asset_df["funding_apr"]) > 10
        ]
    )

    # =========================
    # SCORE
    # =========================

    score = 0

    if persistence >= 3:

        score += 2

    if abs(avg_funding) > 10:

        score += 2

    # =========================
    # DIRECTION
    # =========================

    if avg_funding > 0:

        direction = "SHORT"

    else:

        direction = "LONG"

    # =========================
    # SIGNAL
    # =========================

    signals.append({

        "timestamp": timestamp,

        "asset": asset,

        "funding": avg_funding,

        "persistence": persistence,

        "rsi": 50,

        "trend": "UNKNOWN",

        "score": score,

        "direction": direction,

        "pnl": 0
    })

# =========================
# SAVE TO SQLITE
# =========================

signals_df = pd.DataFrame(
    signals
)

conn = sqlite3.connect(
    "trading_system.db"
)

signals_df.to_sql(

    "signal_memory",

    conn,

    if_exists="append",

    index=False
)

conn.close()

# =========================
# OUTPUT
# =========================

print("\n✅ SIGNAL MEMORY UPDATED")

print(
    f"Signals Added: {len(signals_df)}"
)
