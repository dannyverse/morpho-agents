import sqlite3
import pandas as pd
import os

# =========================
# DATABASE
# =========================

DB_NAME = "trading_system.db"

conn = sqlite3.connect(
    DB_NAME
)

# =========================
# SIGNAL MEMORY
# =========================

if os.path.exists(
    "signal_memory.csv"
):

    df = pd.read_csv(
        "signal_memory.csv"
    )

    df.to_sql(

        "signal_memory",

        conn,

        if_exists="replace",

        index=False
    )

    print(
        "✅ signal_memory migrated"
    )

# =========================
# SYSTEM LOG
# =========================

if os.path.exists(
    "system_log.csv"
):

    df = pd.read_csv(
        "system_log.csv"
    )

    df.to_sql(

        "system_log",

        conn,

        if_exists="replace",

        index=False
    )

    print(
        "✅ system_log migrated"
    )

# =========================
# MODULE HEALTH
# =========================

if os.path.exists(
    "module_health.csv"
):

    df = pd.read_csv(
        "module_health.csv"
    )

    df.to_sql(

        "module_health",

        conn,

        if_exists="replace",

        index=False
    )

    print(
        "✅ module_health migrated"
    )

# =========================
# FUNDING HISTORY
# =========================

if os.path.exists(
    "funding_history.csv"
):

    df = pd.read_csv(
        "funding_history.csv"
    )

    df.to_sql(

        "funding_history",

        conn,

        if_exists="replace",

        index=False
    )

    print(
        "✅ funding_history migrated"
    )

# =========================
# VERIFY TABLES
# =========================

cursor = conn.cursor()

cursor.execute(

    "SELECT name FROM sqlite_master "
    "WHERE type='table';"
)

tables = cursor.fetchall()

print("\n")
print("📦 DATABASE TABLES")
print("=" * 40)

for table in tables:

    print(table[0])

# =========================
# CLOSE
# =========================

conn.close()

print("\n")
print("🚀 Database migration completed")