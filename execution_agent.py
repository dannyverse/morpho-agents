import sqlite3
import pandas as pd
import random
import json

from datetime import datetime
from market_data_manager import (
    refresh_market_data,
    get_price,
    is_market_data_stale,
    get_market_data_age,
    get_market_data_status
)
from telegram_test import send_alert

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

SELECT *

FROM signal_memory

ORDER BY ROWID DESC

LIMIT 30

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

    market_bias = ai_df[
        "market_bias"
    ].iloc[-1]

    decision_health = ai_df[
        "decision_health"
    ].iloc[-1]

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

# =========================
# EXECUTION LOOP
# =========================

executions = []

approved = 0

rejected = 0

for _, row in signals_df.iterrows():

    confidence = round(

        min(

            95,

            60 + row["score"] * 5 + row["persistence"]

        ),

        2
    )

    signal_strength = round(

        min(

            1.0,

            max(

                0.5,

                (row["score"] + row["persistence"]) / 10
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
    # AI MARKET BIAS FILTER
    # =========================

    if (

        market_bias == "SHORT_BIAS"

        and

        row["direction"] == "LONG"
    ):

        confidence -= 10

    elif (

        market_bias == "LONG_BIAS"

        and

        row["direction"] == "SHORT"
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

        print(
            f"\n✅ EXECUTED: "
            f"{row['asset']}"
        )

        telegram_message = (

            f"✅ EXECUTED {row['asset']}\n\n"

            f"Confidence: {confidence}\n"

            f"Signal Strength: {signal_strength}\n"

            f"AI Bias: {market_bias}\n"

            f"Decision Health: {decision_health}\n"

            f"Rationale: {rationale}"
        )

        send_alert(
            telegram_message
        )

    else:

        status = "BLOCKED"

        rejected += 1

        print(
            f"\n❌ REJECTED: "
            f"{row['asset']}"
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

        "score": row["pnl"],

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
# ============================
# POSITION STATE UPDATE
# ============================

position_state = {}

for execution in executions:

    if execution["execution_decision"] != "APPROVED":
        continue

    position_state[
        execution["asset"]
    ] = {

        "status": "OPEN",

        "side": execution["direction"],

        "entry_price": execution["entry_price"],

        "quantity": execution["position_size"],

        "opened_at": execution["timestamp"],

        "exchange": "hyperliquid"
    }

with open(
    "state/position_state.json",
    "w"
) as f:

    json.dump(
        position_state,
        f,
        indent=4
    )
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
