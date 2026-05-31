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

if "position_state" not in tables_df["name"].values:

    print("\n")
    print(
        "No executions table found"
    )

    conn.close()

    exit()

# =========================
# LOAD EXECUTIONS
# =========================

query = """

SELECT *

FROM position_state








"""

df = pd.read_sql_query(

    query,

    conn
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

    current_price = row["current_price"]

    leverage = 1

    position_size = row["position_size"]

    unrealized_pnl = row["position_pnl"]

    position = {

        "timestamp": str(
            datetime.now()
        ),

        "asset": row["asset"],

        "direction": "LONG",

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
