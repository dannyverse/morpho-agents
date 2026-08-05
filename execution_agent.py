import sqlite3
import pandas as pd
import random
import json
import uuid
from decimal import Decimal

from execution_workflow import execute
from execution_authority import can_execute_live
from datetime import datetime, timezone
from account_snapshot import get_account_snapshot

from margin_admission import (
    CandidateOrderV1,
    CandidateSizeStatus,
    CycleContextV1,
    AdmissionPolicyV1,
    MarginMode,
    AdmissionDecision,
    evaluate_margin_admission,
)
from market_data_manager import (
    refresh_market_data,
    get_price,
    is_market_data_stale,
    get_market_data_age,
    get_market_data_status
)

from notifier import (
    notify,
    send_execution_approved
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

    if not exchange_order_id:
        raise ValueError(
            f"Refusing to persist position without exchange_order_id: "
            f"{asset} {direction}"
        )

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

exchange_rate_limited = False

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
    # RECENT EXECUTION COOLDOWN
    # =========================

    cooldown_query = """

    SELECT COUNT(*)

    FROM executions

    WHERE asset=?

    AND direction=?

    AND execution_decision='APPROVED'

    AND status='EXECUTED'

    AND timestamp > datetime(
        'now',
        '-24 hours'
    )

    """

    cooldown_df = pd.read_sql_query(
        cooldown_query,
        conn,
        params=(
            row["asset"],
            row["direction"]
        )
    )

    if int(cooldown_df["COUNT(*)"].iloc[0]) > 0:

        execution_decision = "REJECTED"

        rejection_reason = "RECENT_EXECUTION_COOLDOWN"

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
    # POSITION LIMIT
    # =========================

    if execution_decision == "APPROVED":

        open_positions_df = pd.read_sql_query(
            """
            SELECT COUNT(*) AS count
            FROM positions
            WHERE status='OPEN'
            """,
            conn
        )

        open_positions = int(
            open_positions_df["count"].iloc[0]
        )

        if open_positions >= 25:

            execution_decision = "REJECTED"

            rejection_reason = "POSITION_LIMIT"

    # =========================
    # STATUS
    # =========================

    if exchange_rate_limited:

        status = "FAILED"

        execution_decision = "EXCHANGE_FAILED"

        rejection_reason = "Exchange rate limit already reached this cycle"

        rejected += 1

    elif execution_decision == "APPROVED":

        POSITION_NOTIONAL_USD = 25.0

        price = get_price(row["asset"])

        if price <= 0:

            execution_decision = "REJECTED"
            rejection_reason = "INVALID_MARKET_DATA"

            status = "BLOCKED"

            rejected += 1

            position_size = 0

        else:

            position_size = POSITION_NOTIONAL_USD / price

            snapshot = get_account_snapshot()

            candidate = CandidateOrderV1(
                schema_version="1.0",
                candidate_id=str(uuid.uuid4()),
                cycle_id=cycle_id,
                created_at=datetime.now(timezone.utc),
                asset=row["asset"],
                direction=row["direction"],
                requested_size=position_size,
                reference_price=price,
                reference_price_timestamp=datetime.now(timezone.utc),
                requested_notional=Decimal(str(POSITION_NOTIONAL_USD)),
                margin_mode=MarginMode.CROSS,
                reduce_only=False,
                size_normalization_status=CandidateSizeStatus.NORMALIZED,
            )

            cycle_context = CycleContextV1(
                schema_version="1.0",
                cycle_id=cycle_id,
                account_snapshot_id=snapshot.snapshot_id,
                account_refresh_sequence=1,
                reserved_capacity=Decimal("0"),
                evaluated_candidates=0,
                pending_candidate_ids=(),
                execution_blocked=False,
                block_reason=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            policy = AdmissionPolicyV1(
                schema_version="1.0",
                max_snapshot_age_seconds=Decimal("60"),
                absolute_reserve=Decimal("20"),
                safety_buffer=Decimal("5"),
                supported_margin_mode=MarginMode.CROSS,
                notional_tolerance=Decimal("0.000001"),
            )

            admission_result = evaluate_margin_admission(
                account_snapshot=snapshot,
                candidate_order=candidate,
                cycle_context=cycle_context,
                policy=policy,
            )

            if admission_result.decision != AdmissionDecision.ADMITTED:

                execution_decision = "REJECTED"
                rejection_reason = (
                    admission_result.reason_code.value
                )

        if not can_execute_live():

            execution_decision = "REJECTED"

            rejection_reason = "LIVE_EXECUTION_NOT_AUTHORIZED"

            status = "BLOCKED"

            rejected += 1

        else:

            status = "EXECUTED"

            approved += 1

            execution_result = execute(
                asset=row["asset"],
                direction=row["direction"],
                position_size=position_size,
            )

            print("SUCCESS:", execution_result.success)
            print("ORDER:", execution_result.exchange_order_id)
            print("SL:", execution_result.stop_loss_order_id)
            print("TP:", execution_result.take_profit_order_id)

            if execution_result.success:

                create_position(
                    conn,
                    row["asset"],
                    row["direction"],
                    execution_result.entry_price,
                    position_size,
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
                    entry_price=get_price(row["asset"]),
                    score=row["score"],
                    confidence=confidence,
                    signal_strength=signal_strength,
                    rationale=rationale,
                    market_bias=market_bias,
                    decision_health=decision_health
                )

            elif execution_result.position_open:

                create_position(
                    conn,
                    row["asset"],
                    row["direction"],
                    execution_result.entry_price,
                    position_size,
                    cycle_id,
                    execution_result.exchange_order_id,
                    execution_result.stop_loss_order_id,
                    execution_result.take_profit_order_id
                )

                status = "FAILED"

                execution_decision = "EXCHANGE_FAILED"

                rejection_reason = execution_result.error

                rejected += 1

                notify(
                    level="CRITICAL",
                    title="ROLLBACK FAILED — POSITION OPEN",
                    body="The exchange position remains open after rollback failure.",
                    details={
                        "Asset": row["asset"],
                        "Direction": row["direction"],
                        "Entry": execution_result.entry_price,
                        "Reason": execution_result.error,
                    },
                )

                print(
                    f"\n🚨 EMERGENCY POSITION PERSISTED: {row['asset']}"
                )

            else:

                print(
                    f"\n❌ EXCHANGE EXECUTION FAILED: {row['asset']}"
                )

                status = "FAILED"

                execution_decision = "EXCHANGE_FAILED"

                rejection_reason = execution_result.error

                rejected += 1

    else:

        status = "BLOCKED"

        rejected += 1

        print(
            f"\n❌ REJECTED: {row['asset']} ({rejection_reason})"
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

        "position_size": position_size,

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
