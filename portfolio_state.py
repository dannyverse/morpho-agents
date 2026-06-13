import sqlite3
import pandas as pd
import requests

from datetime import datetime

# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)
def get_current_price(asset):

    try:

        response = requests.post(

            "https://api.hyperliquid.xyz/info",

            json={

                "type": "allMids"

            },
            timeout=5
        )

        prices = response.json()

        return float(

            prices.get(asset, 0)

        )

    except Exception as e:
    
        print(
            f"⚠️ Pricing error for {asset}: {e}"
        )
    
        return 0

        
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

FROM executions

WHERE status='EXECUTED'







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

    current_price = get_current_price(
        row["asset"]
    )

    leverage = 1

    BASE_POSITION_SIZE = 2.0
    
    confidence = row["confidence"]
    
    if confidence >= 85:
        position_size = BASE_POSITION_SIZE * 1.25
    
    elif confidence >= 75:
        position_size = BASE_POSITION_SIZE
    
    else:
        position_size = BASE_POSITION_SIZE * 0.75

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
print(row)
print(row.index)
if "direction" not in row:
    raise Exception("Direction missing from execution payload")

position = {

    "timestamp": str(
        datetime.now()
    ),

    "asset": row["asset"],

    "direction": row["direction"],

    "position_type": f"DIRECTIONAL_{row['direction']}",

    "entry_price": entry_price,

    "current_price": current_price,

    "leverage": leverage,

    "position_size": position_size,

    "unrealized_pnl": unrealized_pnl,

    "realized_pnl": 0,

    "status": "OPEN",
}

positions.append(
    position
)












       

       

        
    

    
        

        

        

        

        

        
    

    
        
    

# =========================
# SAVE
# =========================
# =========================
# SAVE
# =========================

create_query = """

CREATE TABLE IF NOT EXISTS
portfolio_state (

    asset TEXT,

    entry_price REAL,

    current_price REAL,

    position_size REAL,

    unrealized_pnl REAL,

    direction TEXT,

    position_type TEXT,

    status TEXT,

    opened_at TEXT
)

"""

conn.execute(
    create_query
)

positions_df = pd.DataFrame(
    positions
)
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
