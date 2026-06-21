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

refresh_market_data()
    
cycle_query = """

SELECT value

FROM system_state

WHERE key='current_cycle_id'

"""

cycle_df = pd.read_sql_query(

    cycle_query,

    conn
)

cycle_id = cycle_df[
    "value"
].iloc[0]
        

            

            

                

            
        
    

        

        

            

        

    
    
        
            
        
    
        

        
# =========================
# CHECK EXECUTIONS TABLE
# =========================

tables_query = """

SELECT name

FROM sqlite_master

WHERE type='table'

"""

tables_df = pd.read_sql_query(

    tables_query,

    conn
)


# =========================
# LOAD EXECUTIONS
# =========================

query = """

SELECT *

FROM executions

WHERE status='EXECUTED'

AND cycle_id=?

"""

df = pd.read_sql_query(

    query,

    conn,

    params=(
        cycle_id,
    )
)

# =========================
# EMPTY CHECK
# =========================

if len(df) == 0:

    print("\n")
    print(
        "No executions found"
    )

    conn.close()

    exit()

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

    status TEXT
)

"""

conn.execute(
    create_query
)

# =========================
# BUILD POSITIONS
# =========================

positions = []

for _, row in df.iterrows():

    entry_price = row["entry_price"]

    current_price = get_price(
        row["asset"]
    )

    leverage = 1

    BASE_POSITION_SIZE = 2.0

    confidence = row["confidence"]

    if confidence >= 85:

        position_size = (
            BASE_POSITION_SIZE * 1.25
        )

    elif confidence >= 75:

        position_size = (
            BASE_POSITION_SIZE
        )

    else:

        position_size = (
            BASE_POSITION_SIZE * 0.75
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

    position = {

        "timestamp": str(
            datetime.now()
        ),

        "asset": row["asset"],

        "direction": row["direction"],

        "position_type":
            f"DIRECTIONAL_{row['direction']}",

        "entry_price": entry_price,

        "current_price": current_price,

        "leverage": leverage,

        "position_size": position_size,

        "unrealized_pnl": unrealized_pnl,

        "realized_pnl": 0,

        "status": "OPEN"
    }

    positions.append(
        position
    )

# =========================
# SAVE
# =========================

positions_df = pd.DataFrame(
    positions
)

conn.execute(
    "DELETE FROM portfolio_state"
)

positions_df.to_sql(

    "portfolio_state",

    conn,

    if_exists="append",

    index=False
)

# =========================
# VERIFY
# =========================

verify_query = """

SELECT *

FROM portfolio_state

ORDER BY ROWID DESC

LIMIT 10

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
