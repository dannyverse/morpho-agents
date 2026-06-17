import sqlite3
import pandas as pd
import os

from state_manager import (
    StateManager
)

from kill_switch_manager import (
    activate_kill_switch
)

from core.logger import logger
    
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

    "portfolio_state",

    "paper_portfolio",

    "signal_memory"
]

missing_tables = [

    table

    for table in required_tables

    if table not in tables_df["name"].values
]

if len(missing_tables) > 0:

    print("\n")
    print("🛡️ RISK MANAGER")
    print("=" * 50)

    logger.info(
        "risk_manager_started"
    )

    print("\n")

    print(
        "Missing required tables"
    )
    print(
        missing_tables
    )

    print(
        "Risk manager skipped safely"
    )

    conn.close()

    exit()

# =========================
# LOAD DATA
# =========================

portfolio_query = """

SELECT *

FROM portfolio_state

WHERE status='OPEN'

"""

portfolio_df = pd.read_sql_query(
    portfolio_query,
    conn
)

paper_query = """

SELECT *

FROM paper_portfolio

ORDER BY ROWID DESC

LIMIT 1

"""

paper_df = pd.read_sql_query(
    paper_query,
    conn
)

memory_query = """

SELECT *

FROM signal_memory

ORDER BY ROWID DESC

LIMIT 20

"""

memory_df = pd.read_sql_query(
    memory_query,
    conn
)
# =========================
# RUNTIME STATE
# =========================

runtime_state = (
    StateManager.get_runtime_state()
)

runtime_status = "UNKNOWN"

if runtime_state:

    runtime_status = (
        runtime_state.get(
            "system_status",
            "UNKNOWN"
        )
    )
# =========================
# GOVERNANCE LIMITS
# =========================

MAX_EXPOSURE = 150

MAX_OPEN_POSITIONS = 25

MAX_DIRECTIONAL_IMBALANCE = 10

MAX_DRAWDOWN = -20

# =========================
# METRICS
# =========================

open_positions = len(
    portfolio_df
)

long_positions = len(

    portfolio_df[
        portfolio_df[
            "direction"
        ] == "LONG"
    ]
)

short_positions = len(

    portfolio_df[
        portfolio_df[
            "direction"
        ] == "SHORT"
    ]
)

directional_imbalance = abs(

    long_positions -

    short_positions
)

exposure = round(

    paper_df[
        "exposure"
    ].iloc[-1],

    2
)

equity = round(

    paper_df[
        "equity"
    ].iloc[-1],

    2
)

drawdown = round(

    (
        (
            equity - 10000
        )

        / 10000
    ) * 100,

    2
)

recent_pnl = round(

    memory_df[
        "pnl"
    ].sum(),

    2
)

# =========================
# GOVERNANCE FLAGS
# =========================

risk_status = "NORMAL"

kill_switch = False

governance_flags = []

# =========================
# EXPOSURE CHECK
# =========================

if exposure > MAX_EXPOSURE:

    governance_flags.append(
        "EXPOSURE_LIMIT"
    )

# =========================
# POSITION COUNT CHECK
# =========================

if open_positions > MAX_OPEN_POSITIONS:

    governance_flags.append(
        "POSITION_LIMIT"
    )

# =========================
# DIRECTIONAL CHECK
# =========================

if directional_imbalance > MAX_DIRECTIONAL_IMBALANCE:

    governance_flags.append(
        "DIRECTIONAL_IMBALANCE"
    )

# =========================
# DRAWDOWN CHECK
# =========================

if drawdown < MAX_DRAWDOWN:

    governance_flags.append(
        "MAX_DRAWDOWN"
    )

# =========================
# RISK STATUS
# =========================

if len(governance_flags) >= 1:

    risk_status = "DEFENSIVE"

if len(governance_flags) >= 2:

    risk_status = "HIGH_RISK"

if len(governance_flags) >= 3:

    risk_status = "CRITICAL"
if len(governance_flags) > 0:

    logger.warning(
        "governance_flags_triggered",
        flags=governance_flags,
        exposure=exposure,
        directional_imbalance=directional_imbalance,
        risk_status=risk_status
    )

# =========================
# KILL SWITCH ACTIVATION
# =========================

if risk_status == "CRITICAL":

    kill_switch = True

    activate_kill_switch(

        reason="CRITICAL_RISK_STATUS",

        activated_by="risk_manager"
    )

    with open(
        "HALT_TRADING.txt",
        "w"
    ) as f:

        f.write(
            "AUTO KILL SWITCH"
        )
# =========================
# REMOVE KILL SWITCH
# =========================

if risk_status != "CRITICAL":

    if os.path.exists(
        "HALT_TRADING.txt"
    ):

        os.remove(
            "HALT_TRADING.txt"
        )

# =========================
# OUTPUT
# =========================

print("\n")
print("🛡️ RISK MANAGER")
print("=" * 50)

print("\n")
print(
    f"Open Positions: "
    f"{open_positions}"
)

print(
    f"Exposure: "
    f"{exposure}%"
)

print(
    f"Equity: "
    f"${equity}"
)

print(
    f"Drawdown: "
    f"{drawdown}%"
)

print(
    f"Recent PnL: "
    f"{recent_pnl}%"
)

print(
    f"Long Positions: "
    f"{long_positions}"
)

print(
    f"Short Positions: "
    f"{short_positions}"
)

print(
    f"Directional Imbalance: "
    f"{directional_imbalance}"
)

print(
    f"Risk Status: "
    f"{risk_status}"
)

print(
    f"Kill Switch: "
    f"{kill_switch}"
)

print("\n")
print("🚨 GOVERNANCE FLAGS")

print("\n")
print(governance_flags)
print(
    f"Runtime Status: "
    f"{runtime_status}"
)

print("\n")
print("\n")

logger.info(
    "risk_manager_completed",
    risk_status=risk_status,
    open_positions=open_positions,
    exposure=exposure,
    kill_switch=kill_switch
)

print("🚀 Risk manager completed")

conn.close()
