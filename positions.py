import sqlite3
import pandas as pd
import uuid

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

CREATE TABLE IF NOT EXISTS positions (

    position_id TEXT PRIMARY KEY,

    asset TEXT,

    direction TEXT,

    entry_price REAL,

    current_price REAL,

    position_size REAL,

    opened_at TEXT,

    updated_at TEXT,

    status TEXT,

    unrealized_pnl REAL,

    realized_pnl REAL,

    cycle_opened TEXT

)

"""

conn.execute(
    create_query
)

# =========================
# LOAD PORTFOLIO STATE
# =========================

portfolio_query = """

SELECT *

FROM portfolio_state

WHERE status='OPEN'

"""

portfolio_df = pd.read_sql_query(
    portfolio_query,
    conn
)

# =========================
# LOAD POSITIONS
# =========================

positions_df = pd.read_sql_query(

    "SELECT * FROM positions",

    conn
)

# =========================
# BOOTSTRAP POSITIONS
# =========================

created_positions = 0

for _, row in portfolio_df.iterrows():

    existing = positions_df[

        (positions_df["asset"] == row["asset"])

        &

        (positions_df["direction"] == row["direction"])

        &

        (positions_df["status"] == "OPEN")

    ]

    if len(existing) > 0:

        continue

    position = {

        "position_id": str(
            uuid.uuid4()
        ),

        "asset": row["asset"],

        "direction": row["direction"],

        "entry_price": row["entry_price"],

        "current_price": row["current_price"],

        "position_size": row["position_size"],

        "opened_at": row["timestamp"],

        "updated_at": row["timestamp"],

        "status": "OPEN",

        "unrealized_pnl": row["unrealized_pnl"],

        "realized_pnl": row["realized_pnl"],

        "cycle_opened": "BOOTSTRAP"

    }

    pd.DataFrame(
        [position]
    ).to_sql(

        "positions",

        conn,

        if_exists="append",

        index=False
    )

    created_positions += 1

# =========================
# RELOAD POSITIONS
# =========================

positions_df = pd.read_sql_query(

    "SELECT * FROM positions",

    conn
)

open_positions = len(

    positions_df[
        positions_df["status"] == "OPEN"
    ]
)

closed_positions = len(

    positions_df[
        positions_df["status"] == "CLOSED"
    ]
)

conn.close()

# =========================
# OUTPUT
# =========================

print("\n")
print(
    "📂 POSITION STATE"
)

print("=" * 50)

print("\n")

print(
    f"New Positions Created: "
    f"{created_positions}"
)

print(
    f"Open Positions: "
    f"{open_positions}"
)

print(
    f"Closed Positions: "
    f"{closed_positions}"
)

print("\n")

print(
    "✅ Position state ready"
)
