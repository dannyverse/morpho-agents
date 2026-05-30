import pandas as pd
import sqlite3
import os
from datetime import datetime

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

# =========================
# LOAD MARKET REGIME
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
# CLEAN DATA
# =========================

df = df.dropna()

recent = df.tail(20)

# =========================
# METRICS
# =========================

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

winrate = round(

    (wins / len(recent)) * 100,
    2
)

avg_pnl = round(
    recent["pnl"].mean(),
    2
)

# =========================
# RISK STATUS
# =========================

risk_status = "NORMAL"

if avg_pnl < 0:

    risk_status = "DEFENSIVE"

if losses >= 10:

    risk_status = "HIGH_RISK"

# =========================
# SYSTEM STATUS
# =========================

system_status = "RUNNING"

# =========================
# BUILD LOG
# =========================

log = {

    "timestamp": str(
        datetime.now()
    ),

    "market_regime": market_regime,

    "winrate": winrate,

    "avg_pnl": avg_pnl,

    "risk_status": risk_status,

    "system_status": system_status
}

log_df = pd.DataFrame([log])

# =========================
# SAVE TO SQLITE
# =========================

log_df.to_sql(

    "system_log",

    conn,

    if_exists="append",

    index=False
)

# =========================
# VERIFY
# =========================

verify_query = """

SELECT *

FROM system_log

ORDER BY ROWID DESC

LIMIT 5

"""

verify_df = pd.read_sql_query(
    verify_query,
    conn
)

conn.close()

# =========================
# OUTPUT
# =========================

print("\n")
print("📒 SYSTEM LOGGER")
print("=" * 40)

print(
    f"\nSignals Loaded: "
    f"{len(df)}"
)

print(
    f"Market Regime: "
    f"{market_regime}"
)

print(
    f"Winrate: "
    f"{winrate}%"
)

print(
    f"Average PnL: "
    f"{avg_pnl}%"
)

print(
    f"Risk Status: "
    f"{risk_status}"
)

print("\n")
print("🧾 LAST LOG ENTRIES")

print("\n")
print(verify_df)

print("\n")
print("💾 System log saved to SQLite")

print("\n")
print("🚀 Logger completed")