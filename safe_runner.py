import os
import pandas as pd
import sqlite3
from datetime import datetime

from runtime_monitor import (
    write_runtime_state
)

from kill_switch_manager import (
    get_kill_switch_state
)

from core.logger import logger

# =========================
# SYSTEM MODULES
# =========================

modules = [
    "funding_agent.py",
    
    "signal_analytics.py",

    "signal_memory.py",

    "adaptive_scoring.py",

    "portfolio_manager.py",

    "execution_agent.py",

    "meta_intelligence.py",

    "risk_manager.py",

    "portfolio_health_manager.py",

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

failed_modules = []

active_modules = []

cycle_id = int(
    datetime.now().timestamp()
)

logger.info(
    "safe_runner_started",
    cycle_id=cycle_id,
    total_modules=len(modules)
)

# =========================
# KILL SWITCH CHECK
# =========================

kill_switch_state = (
    get_kill_switch_state()
)

if kill_switch_state.get(
    "kill_switch_active",
    False
):

    print("🚨 KILL SWITCH ACTIVE")
    print("=" * 50)

    print("\n")
    print(
        f"Reason: "
        f"{kill_switch_state.get('reason')}"
    )

    print("\n")
    print(
        "🛑 Safe runner aborted"
    )

    exit()
# =========================
# INITIAL RUNTIME STATE
# =========================

write_runtime_state(

    cycle_id=cycle_id,

    system_status="INITIALIZING",

    runtime_mode="NORMAL",

    active_modules=[],

    failed_modules=[],

    heartbeat_ok=True
)

# =========================
# SAFE EXECUTION
# =========================

for module in modules:

    print("\n")
    print("=" * 50)

    print(
        f"\n🚀 Running: {module}"
    )

    logger.info(
        "module_started",
        module=module,
        cycle_id=cycle_id
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

            active_modules.append(
                module
            )

            logger.info(
                "module_completed",
                module=module,
                cycle_id=cycle_id,
                status="SUCCESS"
            )

        else:

            status = "FAILED"

            failed += 1

            failed_modules.append(
                module
            )

            logger.error(
                "module_failed",
                module=module,
                cycle_id=cycle_id,
                status="FAILED"
            )

        results.append({

            "timestamp": str(
                datetime.now()
            ),

            "module": module,

            "status": status
        })

    except Exception as e:

        failed += 1

        failed_modules.append(
            module
        )

        logger.error(
            "module_exception",
            module=module,
            cycle_id=cycle_id,
            error=str(e)
        )

        results.append({

            "timestamp": str(
                datetime.now()
            ),

            "module": module,

            "status": "EXCEPTION",

            "error": str(e)
        })

# SUMMARY# =========================
# FINAL RUNTIME STATUS
# =========================

if failed == 0:

    system_status = "HEALTHY"

    heartbeat_ok = True

else:

    system_status = "DEGRADED"

    heartbeat_ok = False

# =========================
# UPDATE RUNTIME STATE
# =========================

write_runtime_state(

    cycle_id=cycle_id,

    system_status=system_status,

    runtime_mode="NORMAL",

    active_modules=active_modules,

    failed_modules=failed_modules,

    heartbeat_ok=heartbeat_ok,

    last_successful_cycle=cycle_id
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
print(
    f"🩺 Runtime Status: "
    f"{system_status}"
)

print("\n")
print("💾 Health log updated")

print("\n")
print("🚀 Safe runner completed")

logger.info(
    "safe_runner_completed",
    cycle_id=cycle_id,
    successful_modules=success,
    failed_modules=failed
)
