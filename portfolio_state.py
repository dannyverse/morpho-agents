import sqlite3
import pandas as pd

from datetime import datetime

# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

# =========================
# CREATE TABLE
# =========================

create_query = """

CREATE TABLE IF NOT EXISTS
portfolio_state (

    timestamp TEXT,

    asset TEXT,

    direction TEXT,

    entry_price REAL,

    current_price REAL,

    leverage REAL,

    position_size REAL,

    unrealized_pnl REAL,

    realized_pnl REAL,

    status TEXT,

    position_type TEXT
)

"""

conn.execute(
    create_query
)

# =========================
# LOAD OPEN POSITIONS
# =========================

positions_query = """

SELECT *

FROM positions

WHERE status='OPEN'

"""

positions_df = pd.read_sql_query(

    positions_query,

    conn
)

# =========================
# BUILD SNAPSHOT
# =========================

snapshot = []

for _, row in positions_df.iterrows():

    portfolio_row = {

        "timestamp": str(
            datetime.now()
        ),

        "asset": row["asset"],

        "direction": row["direction"],

        "entry_price": row["entry_price"],

        "current_price": row["current_price"],

        "leverage": 1,

        "position_size": row["position_size"],

        "unrealized_pnl": row["unrealized_pnl"],

        "realized_pnl": row["realized_pnl"],

        "status": row["status"],

        "position_type":
            f"DIRECTIONAL_{row['direction']}"
    }

    snapshot.append(
        portfolio_row
    )

# =========================
# SAVE SNAPSHOT
# =========================

snapshot_df = pd.DataFrame(
    snapshot
)

conn.execute(
    "DELETE FROM portfolio_state"
)

snapshot_df.to_sql(

    "portfolio_state",

    conn,

    if_exists="append",

    index=False
)

# =========================
# VERIFY
# =========================

verify_df = pd.read_sql_query(

    """

    SELECT *

    FROM portfolio_state

    ORDER BY ROWID DESC

    LIMIT 10

    """,

    conn
)

conn.close()

# =========================
# OUTPUT
# =========================

print("\n")
print(
    "📂 PORTFOLIO STATE"
)

print("=" * 50)

print("\n")

print(

    verify_df[
        [
            "asset",
            "direction",
            "entry_price",
            "current_price",
            "position_size",
            "unrealized_pnl",
            "status"
        ]
    ]
)

print("\n")

print(
    "🚀 Portfolio state completed"
)
