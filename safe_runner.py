import os
import sys
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
from notifier import notify

# =========================
# SYSTEM MODULES
# =========================

modules = [
    "funding_agent.py",
    
    "signal_analytics.py",

    "signal_memory.py",

    "signal_persistence.py",

    "opportunity_monitor.py",

    "adaptive_scoring.py",

    # "portfolio_manager.py",

    "positions.py",

    "exchange_reconciler.py",

    "execution_agent.py",

    "meta_intelligence.py",

    "portfolio_state.py",

    "risk_manager.py",

    "portfolio_health_manager.py",

    "paper_portfolio.py",

    # "position_manager.py",

    # "strategy_analytics.py",

    "logger.py"
]

# =========================
# CRITICAL EXECUTION GATES
# =========================

CRITICAL_PRE_EXECUTION_MODULES = {
    "positions.py",
    "exchange_reconciler.py",
}

# =========================
# TRACKING
# =========================

success = 0

failed = 0

results = []

failed_modules = []

active_modules = []

execution_blocked = False

cycle_id = int(
    datetime.now().timestamp()
)
# =========================
# UPDATE CURRENT CYCLE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS system_state (

        key TEXT PRIMARY KEY,

        value TEXT
    )
    """
)

conn.execute(
    """
    INSERT OR REPLACE INTO system_state
    (
        key,
        value,
        updated_at
    )
    VALUES (?,?,?)
    """,
    (
        "current_cycle_id",
        str(cycle_id),
        str(datetime.now())
    )
)

conn.commit()

conn.close()
logger.info(
    "safe_runner_started",
    cycle_id=cycle_id,
    total_modules=len(modules)
)

# =========================
# KILL SWITCH CHECK
# =========================

kill_switch_state = get_kill_switch_state()

if kill_switch_state.get(
    "kill_switch_active",
    False
):

    kill_switch_reason = (
        kill_switch_state.get("reason")
    )

    print("🚨 KILL SWITCH ACTIVE")
    print("=" * 50)
    print(f"\nReason: {kill_switch_reason}")
    print("\n🔄 Starting controlled recovery")

    logger.warning(
        "kill_switch_recovery_started",
        cycle_id=cycle_id,
        reason=kill_switch_reason
    )

    recovery_modules = [
        "positions.py",
        "portfolio_state.py",
        "risk_manager.py"
    ]

    for recovery_module in recovery_modules:

        print(
            f"\n🔄 Recovery module: "
            f"{recovery_module}"
        )

        recovery_exit_code = os.system(
            f"{sys.executable} "
            f"{recovery_module}"
        )

        if recovery_exit_code != 0:

            logger.error(
                "kill_switch_recovery_failed",
                cycle_id=cycle_id,
                module=recovery_module,
                exit_code=recovery_exit_code
            )

            print(
                f"\n❌ Recovery failed: "
                f"{recovery_module}"
            )

            print(
                "\n🛑 Safe runner aborted"
            )

            sys.exit(10)

    kill_switch_state = (
        get_kill_switch_state()
    )

    if kill_switch_state.get(
        "kill_switch_active",
        False
    ):

        logger.warning(
            "kill_switch_remains_active",
            cycle_id=cycle_id,
            reason=kill_switch_state.get(
                "reason"
            )
        )

        print(
            "\n🛑 Kill Switch remains active"
        )

        print(
            f"Reason: "
            f"{kill_switch_state.get('reason')}"
        )

        sys.exit(10)

    logger.info(
        "kill_switch_recovery_completed",
        cycle_id=cycle_id
    )

    print(
        "\n✅ Risk status recovered"
    )

    print(
        "✅ Normal cycle will continue"
    )

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

    if module == "execution_agent.py" and execution_blocked:

        status = "BLOCKED"

        failed_modules.append(
            module
        )

        results.append({

            "timestamp": str(
                datetime.now()
            ),

            "module": module,

            "status": status

        })

        print(
            "🛑 execution_agent blocked due to critical module failure"
        )

        continue

    try:

        exit_code = os.system(
            f"{sys.executable} {module}"
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

            if module in CRITICAL_PRE_EXECUTION_MODULES:

                execution_blocked = True

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

# =========================
# CRITICAL ALERT
# =========================

if failed > 0:

    notify(
        level="ERROR",
        title="MORPHO RUNTIME ALERT",
        body="One or more runtime modules failed.",
        details={
            "failed_modules": failed,
            "runtime_status": system_status,
            "action": "Review required",
        },
    )

logger.info(
    "safe_runner_completed",
    cycle_id=cycle_id,
    successful_modules=success,
    failed_modules=failed
)

# =========================
# EXIT STATUS
# =========================

if failed > 0:

    sys.exit(20)

sys.exit(0)
