import sqlite3
import pandas as pd

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
        "Strategy analytics skipped safely"
    )

    conn.close()

    exit()

# =========================
# LOAD EXECUTIONS
# =========================

query = """

SELECT *

FROM executions

"""

df = pd.read_sql_query(
    query,
    conn
)

conn.close()

# =========================
# EMPTY CHECK
# =========================

if len(df) == 0:

    print("\n")

    print(
        "No executions found"
    )

    exit()

# =========================
# STRATEGY METRICS
# =========================

approved = len(

    df[
        df[
            "execution_decision"
        ] == "APPROVED"
    ]
)

rejected = len(

    df[
        df[
            "execution_decision"
        ] == "REJECTED"
    ]
)

approval_rate = round(

    approved /

    len(df) * 100,

    2
)

avg_confidence = round(

    df[
        "confidence"
    ].mean(),

    2
)

avg_signal_strength = round(

    df[
        "signal_strength"
    ].mean(),

    2
)

# =========================
# REJECTION BREAKDOWN
# =========================

rejection_stats = df[

    "rejection_reason"

].value_counts()

# =========================
# RATIONALE BREAKDOWN
# =========================

rationale_stats = df[

    "rationale"

].value_counts()

# =========================
# OUTPUT
# =========================

print("\n")
print("=" * 60)

print(
    "\n🧠 STRATEGY ANALYTICS"
)

print("=" * 60)

print("\n")

print(
    f"Total Executions: "
    f"{len(df)}"
)

print(
    f"Approved: "
    f"{approved}"
)

print(
    f"Rejected: "
    f"{rejected}"
)

print(
    f"Approval Rate: "
    f"{approval_rate}%"
)

print(
    f"Average Confidence: "
    f"{avg_confidence}"
)

print(
    f"Average Signal Strength: "
    f"{avg_signal_strength}"
)

print("\n")
print("🚨 REJECTION BREAKDOWN")

print("\n")

print(
    rejection_stats
)

print("\n")
print("🧠 RATIONALE BREAKDOWN")

print("\n")

print(
    rationale_stats
)

print("\n")
print("🚀 Strategy analytics completed")