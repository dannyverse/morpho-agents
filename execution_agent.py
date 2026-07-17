import sqlite3
import pandas as pd
import random
import json
import uuid

from datetime import datetime
from market_data_manager import (
    refresh_market_data,
    get_price,
    is_market_data_stale,
    get_market_data_age,
    get_market_data_status
)
from notifier import (
    send_alert,
    send_execution_approved
)

from execution_workflow import execute

from positions import (
    calculate_stop_loss,
    calculate_take_profit
)

def create_position(
    conn,
    asset,
    direction,
    entry_price,
    position_size,
    cycle_id,
    exchange_order_id=None,
    stop_loss_order_id=None,
    take_profit_order_id=None
):
    now = str(datetime.now())

    conn.execute(
        """
        INSERT INTO positions (
            position_id,
            asset,
            direction,
            entry_price,
            current_price,
            position_size,
            opened_at,
            updated_at,
            status,
            unrealized_pnl,
            realized_pnl,
            cycle_opened,
            exchange_order_id,
            stop_loss_order_id,
            take_profit_order_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            asset,
            direction,
            entry_price,
            entry_price,
            position_size,
            now,
            now,
            "OPEN",
            0.0,
            0.0,
            cycle_id,
            exchange_order_id,
            stop_loss_order_id,
            take_profit_order_id
        )
    )
# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

refresh_market_data()
if is_market_data_stale():

    print(
        f"⚠️ WARNING: Market data is stale ({get_market_data_age()} seconds old)"
    )        
cycle_query = """

SELECT value

FROM system_state

WHERE key='current_cycle_id'

"""

cycle_df = pd.read_sql_query(
    cycle_query,
    conn
)

cycle_id = cycle_df[
    "value"
].iloc[0]

# =========================
# LOAD SIGNALS
# =========================

signals_query = """

SELECT sm.*

FROM signal_memory sm

INNER JOIN (

    SELECT

        asset,

        MAX(rowid) AS max_rowid

    FROM signal_memory

    GROUP BY asset

) latest

ON sm.rowid = latest.max_rowid

ORDER BY sm.score DESC,
         sm.persistence DESC

"""


signals_df = pd.read_sql_query(

    signals_query,

    conn
)

# =========================
# LOAD AI REASONING
# =========================

ai_query = """

SELECT *

FROM ai_reasoning

ORDER BY ROWID DESC

LIMIT 1

"""

try:

    ai_df = pd.read_sql_query(

        ai_query,

        conn
    )

except:

    ai_df = pd.DataFrame()

# =========================
# AI CONTEXT
# =========================

market_bias = "NEUTRAL"

decision_health = "NORMAL"

if len(ai_df) > 0:

    market_bias = ai_df["market_bias"].iloc[-1]
    decision_health = ai_df["risk_level"].iloc[-1]

else:

    market_bias = "NEUTRAL"
    decision_health = "NORMAL"

# =========================
# CREATE TABLE
# =========================

create_query = """

CREATE TABLE IF NOT EXISTS
executions (

    timestamp TEXT,

    asset TEXT,

    direction TEXT,

    score REAL,

    confidence REAL,

    entry_price REAL,

    position_size REAL,

    cycle_id TEXT,

    signal_strength REAL,

    regime TEXT,

    governance_status TEXT,

    rationale TEXT,

    execution_decision TEXT,

    rejection_reason TEXT,

    status TEXT
)

"""

conn.execute(
    create_query
)

# =========================
# GOVERNANCE THRESHOLDS
# =========================

MIN_CONFIDENCE = 70

MIN_SIGNAL_STRENGTH = 0.65

# =========================
# AI ADAPTATION
# =========================

if decision_health == "DEFENSIVE":

    MIN_CONFIDENCE = 80

    MIN_SIGNAL_STRENGTH = 0.75

elif decision_health == "HIGH_RISK":

    MIN_CONFIDENCE = 85

    MIN_SIGNAL_STRENGTH = 0.85

print(
    f"DEBUG -> decision_health={decision_health}, "
    f"MIN_CONFIDENCE={MIN_CONFIDENCE}, "
    f"market_bias={market_bias}"
)

# =========================
# EXECUTION LOOP
# =========================

executions = []

approved = 0

rejected = 0

for _, row in signals_df.iterrows():

    effective_persistence = min(
        row["persistence"],
        10
    )

    confidence = round(
        min(
            95,
            60 + (row["score"] / 8.0) * 35
        ),
        2
    )
    signal_strength = round(
        min(
            1.0,
            max(
                0.5,
                (
                    row["score"]
                    + effective_persistence
                ) / 18.0
            )
        ),
        2
    )

    if row["persistence"] >= 5:

        rationale = "persistent funding anomaly"

    elif abs(row["funding"]) > 20:

        rationale = "extreme funding imbalance"

    elif row["score"] >= 4:

        rationale = "high opportunity score"

    else:

        rationale = "moderate opportunity"

    execution_decision = "APPROVED"

    rejection_reason = "NONE"

    # =========================
    # DUPLICATE PREVENTION
    # =========================

    duplicate_query = """

    SELECT *

    FROM positions

    WHERE asset=?

    AND direction=?

    AND status='OPEN'

    """

    duplicate_df = pd.read_sql_query(

        duplicate_query,

        conn,

        params=(

            row["asset"],

            row["direction"]

        )
    )

    if len(duplicate_df) > 0:

        execution_decision = "REJECTED"

        rejection_reason = "DUPLICATE_POSITION"

    # =========================
    # AI MARKET BIAS FILTER
    # =========================

    if (
        market_bias == "SHORT_BIAS"
        and row["direction"] == "LONG"
    ):

        confidence -= 10

    elif (
        market_bias == "LONG_BIAS"
        and row["direction"] == "SHORT"
    ):

        confidence -= 10

    # =========================
    # GOVERNANCE FILTERS
    # =========================

    if confidence < MIN_CONFIDENCE:

        execution_decision = "REJECTED"

        rejection_reason = "LOW_CONFIDENCE"

    elif signal_strength < MIN_SIGNAL_STRENGTH:

        execution_decision = "REJECTED"

        rejection_reason = "WEAK_SIGNAL"

    # =========================
    # STATUS
    # =========================

    if execution_decision == "APPROVED":

        status = "EXECUTED"

        approved += 1

        execution_result = execute(
            asset=row["asset"],
            direction=row["direction"],
            position_size=2.5,
        )

        if not execution_result.success:

            print(
                f"\n❌ EXCHANGE EXECUTION FAILED: {row['asset']}"
            )

            rejected += 1

            continue

        create_position(
            conn,
            row["asset"],
            row["direction"],
            execution_result.entry_price,
            2.5,
            cycle_id,
            execution_result.exchange_order_id,
            execution_result.stop_loss_order_id,
            execution_result.take_profit_order_id
        )

        print(
            f"\n✅ EXECUTED: {row['asset']}"
        )

        send_execution_approved(
            asset=row["asset"],
            direction=row["direction"],
            entry_price=get_price(
                row["asset"]
            ),
            score=row["score"],
            confidence=confidence,
            signal_strength=signal_strength,
            rationale=rationale,
            market_bias=market_bias,
            decision_health=decision_health
        )

    else:

        status = "BLOCKED"

        rejected += 1

        print(
            f"\n❌ REJECTED: {row['asset']}"
        )

    # =========================
    # BUILD EXECUTION
    # =========================

    execution = {

        "timestamp": str(
            datetime.now()
        ),

        "asset": row["asset"],

        "direction": row["direction"],

        "score": row["score"],

        "confidence": confidence,

        "entry_price": get_price(
            row["asset"]
        ),

        "position_size": 2.5,

        "signal_strength": signal_strength,

        "regime": market_bias,

        "governance_status": decision_health,

        "rationale": rationale,

        "execution_decision": execution_decision,

        "rejection_reason": rejection_reason,

        "cycle_id": cycle_id,

        "status": status
    }

    executions.append(
        execution
    )


# =========================
# SAVE
# =========================

executions_df = pd.DataFrame(
    executions
)

executions_df.to_sql(

    "executions",

    conn,

    if_exists="append",

    index=False
)

conn.close()

# =========================
# SUMMARY
# =========================

print("\n")
print("=" * 60)

print(
    "🧠 AI GOVERNED EXECUTION ENGINE"
)

print("=" * 60)

print("\n")

print(
    f"AI Market Bias: "
    f"{market_bias}"
)

print(
    f"Decision Health: "
    f"{decision_health}"
)

market_data_status = get_market_data_status()
if market_data_status in ["CRITICAL", "UNKNOWN"]:

    print(
        "\n🚨 EXECUTION BLOCKED:"
        " Market data infrastructure"
        " is not trustworthy\n"
    )

    exit()
status_icon = "✅"

if market_data_status == "WARNING":
    status_icon = "⚠️"

elif market_data_status == "CRITICAL":
    status_icon = "🚨"

elif market_data_status == "UNKNOWN":
    status_icon = "❓"

print(
    f"Market Data Status: "
    f"{status_icon} "
    f"{market_data_status}"
)    

print("\n")

print(
    f"Approved Executions: "
    f"{approved}"
)

print(
    f"Rejected Executions: "
    f"{rejected}"
)

print("\n")
print(
    "🚀 Execution agent completed"
)
