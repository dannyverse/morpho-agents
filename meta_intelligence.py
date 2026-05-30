import pandas as pd
import sqlite3

# =========================
# LOAD DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

query = """

SELECT *

FROM signal_memory

"""

df = pd.read_sql_query(
    query,
    conn
)

conn.close()

# =========================
# CLEAN DATA
# =========================

df = df.dropna()

# =========================
# RECENT PERFORMANCE
# =========================

recent = df.tail(20)

wins = len(

    recent[
        recent["pnl"] > 0
    ]
)

losses = len(

    recent[
        recent["pnl"] <= 0
    ]
)

avg_pnl = round(

    recent["pnl"].mean(),
    2
)

winrate = round(

    (wins / len(recent)) * 100,
    2
)

# =========================
# REGIME DETECTION
# =========================

if avg_pnl > 1 and winrate > 60:

    regime = "AGGRESSIVE"

elif avg_pnl < 0 and winrate < 50:

    regime = "DEFENSIVE"

else:

    regime = "NEUTRAL"

# =========================
# RISK MULTIPLIER
# =========================

risk_multiplier = 1.0

if regime == "AGGRESSIVE":

    risk_multiplier = 1.5

elif regime == "DEFENSIVE":

    risk_multiplier = 0.5

# =========================
# STREAK DETECTION
# =========================

recent_pnls = recent[
    "pnl"
].tolist()

win_streak = 0
loss_streak = 0

for pnl in reversed(
    recent_pnls
):

    if pnl > 0:

        if loss_streak == 0:

            win_streak += 1

        else:

            break

    else:

        if win_streak == 0:

            loss_streak += 1

        else:

            break

# =========================
# SAVE REGIME
# =========================

with open(
    "market_regime.txt",
    "w"
) as f:

    f.write(regime)

# =========================
# OUTPUT
# =========================

print("\n")
print("🧠 META INTELLIGENCE")
print("=" * 40)

print(
    f"\nSignals Loaded: "
    f"{len(df)}"
)

print(
    f"Recent Winrate: "
    f"{winrate}%"
)

print(
    f"Recent Avg PnL: "
    f"{avg_pnl}%"
)

print(
    f"Market Regime: "
    f"{regime}"
)

print(
    f"Risk Multiplier: "
    f"{risk_multiplier}"
)

print(
    f"Win Streak: "
    f"{win_streak}"
)

print(
    f"Loss Streak: "
    f"{loss_streak}"
)

print("\n")
print("💾 Market regime updated")

print("\n")
print("🚀 Meta intelligence completed")