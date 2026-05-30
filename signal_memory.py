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
# RECENT SIGNALS
# =========================

recent = df.tail(20)

# =========================
# PERFORMANCE
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
# OUTPUT
# =========================

print("\n")
print("📚 SIGNAL MEMORY")
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

print("\n")
print(
    recent[
        [
            "asset",
            "direction",
            "pnl"
        ]
    ].tail(10)
)

print("\n")
print("🚀 Signal memory completed")