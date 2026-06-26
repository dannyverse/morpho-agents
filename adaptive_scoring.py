import pandas as pd
import sqlite3

# =========================
# LOAD MEMORY
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

df = pd.read_sql_query(
    "SELECT * FROM signal_memory",
    conn
)

conn.close()

# =========================
# WINRATE BY ASSET
# =========================

results = []

assets = df["asset"].unique()

for asset in assets:

    asset_df = df[
        df["asset"] == asset
    ]

    total = len(asset_df)

    wins = len(
        asset_df[
            asset_df["pnl"] > 0
        ]
    )

    losses = len(
        asset_df[
            asset_df["pnl"] <= 0
        ]
    )

    winrate = round(
        (wins / total) * 100,
        2
    )

    avg_pnl = round(
        asset_df["pnl"].mean(),
        2
    )

    # =========================
    # ADAPTIVE WEIGHT
    # =========================

    weight = 1.0

    if winrate > 60:

        weight += 0.5

    if avg_pnl > 1:

        weight += 0.5

    if losses > wins:

        weight -= 0.3

    results.append({

        "asset": asset,

        "trades": total,

        "wins": wins,

        "losses": losses,

        "winrate": winrate,

        "avg_pnl": avg_pnl,

        "adaptive_weight": round(
            weight,
            2
        )
    })

# =========================
# RESULTS
# =========================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="adaptive_weight",
    ascending=False
)

# =========================
# OUTPUT
# =========================

print("\n🧠 ADAPTIVE SCORING ENGINE\n")

print(results_df.head(20))
