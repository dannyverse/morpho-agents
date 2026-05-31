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
# CHECK TABLES
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

required_tables = [

    "portfolio_state"
]

    

missing_tables = [

    table

    for table in required_tables

    if table not in tables_df["name"].values
]

if len(missing_tables) > 0:

    print("\n")

    print(
        "Missing required tables"
    )

    print(
        missing_tables
    )

    print(
        "Paper portfolio skipped safely"
    )

    conn.close()

    exit()

# =========================
# LOAD EXECUTIONS
# =========================

query = """

SELECT *

FROM portfolio_state



"""

portfolio_df = pd.read_sql_query(
    query,
    conn
)

# =========================
# EMPTY CHECK
# =========================

if len(portfolio_df) == 0:

    print("\n")

    print(
        "No approved executions"
    )

    conn.close()

    exit()

# =========================
# CREATE PNL
# =========================

total_pnl = round(

    portfolio_df[
        "unrealized_pnl"
    ].sum(),

    2
)




# =========================
# PORTFOLIO METRICS
# =========================

starting_equity = 10000

total_pnl = round(

portfolio_df[
        "unrealized_pnl"
    ].sum(),

    2
)

equity = round(

    starting_equity +

    total_pnl,

    2
)

open_positions = len(portfolio_df)
exposure = round(

portfolio_df[
    "position_size"
].sum() / 100,
    2
)

# =========================
# CREATE TABLE
# =========================

create_query = """

CREATE TABLE IF NOT EXISTS
paper_portfolio (

    timestamp TEXT,

    equity REAL,

    exposure REAL,

    open_positions INTEGER,

    unrealized_pnl REAL
)

"""

conn.execute(
    create_query
)

# =========================
# SAVE SNAPSHOT
# =========================

snapshot = pd.DataFrame([{

    "timestamp": str(
        datetime.now()
    ),

    "equity": equity,

    "exposure": exposure,

    "open_positions": open_positions,

    "unrealized_pnl": total_pnl
}])

snapshot.to_sql(

    "paper_portfolio",

    conn,

    if_exists="append",

    index=False
)

# =========================
# VERIFY
# =========================

verify_query = """

SELECT *

FROM paper_portfolio

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
print("=" * 60)

print(
    "\n💼 PAPER PORTFOLIO"
)

print("=" * 60)

print("\n")

print(
    f"Equity: ${equity}"
)

print(
    f"Exposure: {exposure}%"
)

print(
    f"Open Positions: "
    f"{open_positions}"
)

print(
    f"Unrealized PnL: "
    f"{total_pnl}%"
)

print("\n")
print("📂 RECENT SNAPSHOTS")

print("\n")

print(
    verify_df
)

print("\n")
print("🚀 Paper portfolio completed")
