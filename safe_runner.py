import os
import pandas as pd
import sqlite3
from datetime import datetime

# =========================
# SYSTEM MODULES
# =========================

modules = [

    "signal_analytics.py",

    "signal_memory.py",

    "adaptive_scoring.py",

    "portfolio_manager.py",

    "execution_agent.py",

    "meta_intelligence.py",

    "risk_manager.py",

    "portfolio_state.py",

    "paper_portfolio.py",

    "position_manager.py",

    "strategy_analytics.py",

    "logger.py"
]

# =========================
# TRACKING
# =========================

success = 0

failed = 0

results = []

# =========================
# SAFE EXECUTION
# =========================

for module in modules:

    print("\n")
    print("=" * 50)

    print(
        f"\n🚀 Running: {module}"
    )

    try:

        exit_code = os.system(
            f"python {module}"
        )

        # =========================
        # STATUS
        # =========================

        if exit_code == 0:

            status = "SUCCESS"

            success += 1

        else:

            status = "FAILED"

            failed += 1

        results.append({

            "timestamp": str(
                datetime.now()
            ),

            "module": module,

            "status": status
        })

    except Exception as e:

        failed += 1

        results.append({

            "timestamp": str(
                datetime.now()
            ),

            "module": module,

            "status": "CRASHED"
        })

        print("\n")

        print(
            f"❌ Crash: {module}"
        )

        print(
            str(e)
        )

# =========================
# HEALTH TABLE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

create_query = """

CREATE TABLE IF NOT EXISTS
system_health (

    timestamp TEXT,

    module TEXT,

    status TEXT
)

"""

conn.execute(
    create_query
)

# =========================
# SAVE HEALTH LOG
# =========================

health_df = pd.DataFrame(
    results
)

health_df.to_sql(

    "system_health",

    conn,

    if_exists="append",

    index=False
)

conn.close()

# =========================
# OUTPUT
# =========================

print("\n")
print("=" * 60)

print(
    f"\n✅ Success: {success}"
)

print(
    f"❌ Failed: {failed}"
)

print("\n")
print("💾 Health log updated")

print("\n")
print("🚀 Safe runner completed")