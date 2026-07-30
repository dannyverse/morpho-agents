import sqlite3
import pandas as pd

from datetime import datetime

from market_data_manager import (
    refresh_market_data,
    get_price
)
# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

def calculate_stop_loss(entry_price, direction):

    if direction == "LONG":
        return entry_price * 0.98

    return entry_price * 1.02

def calculate_take_profit(entry_price, direction):

    if direction == "LONG":
        return entry_price * 1.04

    return entry_price * 0.96

def close_position(conn, position_id, realized_pnl):
    conn.execute(
        """
        UPDATE positions
        SET
            status='CLOSED',
            realized_pnl=?,
            updated_at=?
        WHERE position_id=?
        """,
        (
            realized_pnl,
            str(datetime.now()),
            position_id,
        ),
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

    stop_loss_price REAL,

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
# LOAD POSITIONS
# =========================

positions_df = pd.read_sql_query(

    "SELECT * FROM positions",

    conn
)

# =========================
# REFRESH MARKET DATA
# =========================

refresh_market_data()

# =========================
# UPDATE OPEN POSITIONS
# =========================

positions_df = pd.read_sql_query(

    """

    SELECT *

    FROM positions

    WHERE status='OPEN'

    """,

    conn
)

updated_positions = 0

for _, row in positions_df.iterrows():

    entry_price = row["entry_price"]

    current_price = get_price(
        row["asset"]
    )

    if entry_price > 0:

        if row["direction"] == "LONG":

            unrealized_pnl = round(

                (
                    (
                        current_price
                        -
                        entry_price
                    )
                    /
                    entry_price
                ) * 100,

                2
            )

        else:

            unrealized_pnl = round(

                (
                    (
                        entry_price
                        -
                        current_price
                    )
                    /
                    entry_price
                ) * 100,

                2
            )

    else:

        unrealized_pnl = 0


    conn.execute(

        """

        UPDATE positions

        SET

            current_price=?,

            unrealized_pnl=?,

            updated_at=?

        WHERE position_id=?

        """,

        (

            current_price,

            unrealized_pnl,

            str(datetime.now()),

            row["position_id"]

        )

    )

    updated_positions += 1

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
conn.commit()

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
    f"Updated Positions: "
    f"{updated_positions}"
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
