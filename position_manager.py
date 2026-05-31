import sqlite3
import pandas as pd
import random

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

    "executions"
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
        "Position manager skipped safely"
    )

    conn.close()

    exit()

# =========================
# LOAD EXECUTIONS
# =========================

cycle_query = """

SELECT value

FROM system_state

WHERE key='current_cycle_id'

"""

cycle_df = pd.read_sql_query(
    cycle_query,
    conn
)

current_cycle_id = cycle_df[
    "value"
].iloc[0]

query = """

SELECT *

FROM executions

WHERE execution_decision='APPROVED'

AND cycle_id = ?

"""

df = pd.read_sql_query(
    query,
    conn,
    params=[current_cycle_id]
)










    
  

# =========================
# EMPTY CHECK
# =========================

if len(df) == 0:

    print("\n")

    print(
        "No approved executions"
    )

    conn.close()

    exit()

# =========================
# CREATE POSITION DATA
# =========================

df[
    "entry_price"
] = [

    round(

        random.uniform(10, 200),

        2
    )

    for _ in range(len(df))
]

df[
    "current_price"
] = [

    round(

        entry *

        random.uniform(0.95, 1.08),

        2
    )

    for entry in df[
        "entry_price"
    ]
]

df[
    "position_size"
] = [

    round(

        random.uniform(100, 1000),

        2
    )

    for _ in range(len(df))
]

# =========================
# POSITION PNL
# =========================

df[
    "position_pnl"
] = round(

    (

        (
            df[
                "current_price"
            ]

            -

            df[
                "entry_price"
            ]
        )

        /

        df[
            "entry_price"
        ]

    ) * 100,

    2
)

# =========================
# CREATE TABLE
# =========================

create_query = """

CREATE TABLE IF NOT EXISTS
position_state (

    asset TEXT,

    entry_price REAL,

    current_price REAL,

    position_size REAL,

    position_pnl REAL
)

"""

conn.execute(
    create_query
)

# =========================
# RESET TABLE
# =========================

conn.execute(
    "DELETE FROM position_state"
)

# =========================
# SAVE POSITIONS
# =========================

positions = df.groupby(
    "asset",
    as_index=False
).agg(
    {
        "entry_price": "mean",
        "current_price": "mean",
        "position_size": "sum",
        "position_pnl": "mean"
    }
)
    
        
        
        
       
        
    


positions.to_sql(

    "position_state",

    conn,

    if_exists="append",

    index=False
)

# =========================
# VERIFY
# =========================

verify_query = """

SELECT *

FROM position_state

ORDER BY position_pnl DESC

LIMIT 10

"""

verify_df = pd.read_sql_query(
    verify_query,
    conn
)

conn.close()

# =========================
# PORTFOLIO SUMMARY
# =========================

avg_pnl = round(

    positions[
        "position_pnl"
    ].mean(),

    2
)

best_trade = round(

    positions[
        "position_pnl"
    ].max(),

    2
)

worst_trade = round(

    positions[
        "position_pnl"
    ].min(),

    2
)

# =========================
# OUTPUT
# =========================

print("\n")
print("=" * 60)

print(
    "\n📊 POSITION MANAGER"
)

print("=" * 60)

print("\n")

print(
    f"Open Positions: "
    f"{len(positions)}"
)

print(
    f"Average Position PnL: "
    f"{avg_pnl}%"
)

print(
    f"Best Trade: "
    f"{best_trade}%"
)

print(
    f"Worst Trade: "
    f"{worst_trade}%"
)

print("\n")
print("📂 TOP POSITIONS")

print("\n")

print(
    verify_df
)

print("\n")
print("🚀 Position manager completed")
