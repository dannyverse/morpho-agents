import sqlite3
import pandas as pd
import os

from datetime import datetime

from notifier import send_alert

# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

# =========================
# LOAD EXECUTIONS
# =========================

executions_query = """

SELECT *

FROM executions

ORDER BY ROWID DESC

LIMIT 20

"""

executions_df = pd.read_sql_query(

    executions_query,

    conn
)

# =========================
# LOAD MARKET MAKER SIGNALS
# =========================

mm_query = """

SELECT *

FROM market_maker_signals

ORDER BY ROWID DESC

LIMIT 20

"""

try:

    mm_df = pd.read_sql_query(

        mm_query,

        conn
    )

except:

    mm_df = pd.DataFrame()

# =========================
# AI ANALYSIS
# =========================

market_bias = "NEUTRAL"

decision_health = "NORMAL"

ai_commentary = []

# =========================
# MARKET MAKER ANALYSIS
# =========================

if len(mm_df) > 0:

    crowded_longs = len(

        mm_df[
            mm_df["rationale"]

            ==

            "crowded_longs"
        ]
    )

    crowded_shorts = len(

        mm_df[
            mm_df["rationale"]

            ==

            "crowded_shorts"
        ]
    )

    if crowded_longs > crowded_shorts:

        market_bias = "SHORT_BIAS"

        ai_commentary.append(

            "Long positioning overcrowded."
        )

    elif crowded_shorts > crowded_longs:

        market_bias = "LONG_BIAS"

        ai_commentary.append(

            "Short positioning overcrowded."
        )

# =========================
# EXECUTION ANALYSIS
# =========================

approval_rate = 1

avg_confidence = 100

if len(executions_df) > 0:

    avg_confidence = round(

        executions_df[
            "confidence"
        ].mean(),

        2
    )

    approval_rate = round(

        len(

            executions_df[
                executions_df[
                    "execution_decision"
                ]

                ==

                "APPROVED"
            ]
        )

        /

        len(executions_df),

        2
    )

    if avg_confidence < 75:

        decision_health = "DEFENSIVE"

        ai_commentary.append(

            "Execution confidence weakening."
        )

#    if approval_rate < 0.4:

#        decision_health = "HIGH_RISK"

#        ai_commentary.append(

#            "Governance rejecting most signals."
#        )


# =========================
# HALT LOGIC
# =========================

halt_recommendation = False

if decision_health == "HIGH_RISK":

    halt_recommendation = True
    ai_commentary.append(

        "Halt recommendation issued."
    )

else:

    ai_commentary.append(

        "No halt recommendation."
    )

# =========================
# FINAL SUMMARY
# =========================

summary = " ".join(
    ai_commentary
)

# =========================
# BUILD RESULT
# =========================

result = {

    "timestamp": str(
        datetime.now()
    ),

    "market_bias": market_bias,

    "decision_health": decision_health,

    "ai_summary": summary
}

result_df = pd.DataFrame(
    [result]
)

# =========================
# CREATE TABLE
# =========================

create_query = """

CREATE TABLE IF NOT EXISTS
ai_reasoning (

    timestamp TEXT,

    market_bias TEXT,

    decision_health TEXT,

    ai_summary TEXT
)

"""

conn.execute(
    create_query
)

# =========================
# SAVE
# =========================

result_df.to_sql(

    "ai_reasoning",

    conn,

    if_exists="append",

    index=False
)

conn.close()

# =========================
# TELEGRAM
# =========================

telegram_message = (

    f"🧠 AI MARKET REASONING\n\n"

    f"Market Bias: {market_bias}\n"

    f"Decision Health: {decision_health}\n"

    f"Halt Recommendation: {halt_recommendation}\n\n"

    f"{summary}"
)

send_alert(
    telegram_message
)

# =========================
# OUTPUT
# =========================

print("\n")
print("=" * 60)

print(
    "🧠 AI REASONING LAYER"
)

print("=" * 60)

print("\n")

print(
    f"Market Bias: "
    f"{market_bias}"
)

print(
    f"Decision Health: "
    f"{decision_health}"
)

print(
    f"Halt Active: "
    f"{halt_recommendation}"
)

print("\n")

print(
    summary
)

print("\n")
print(
    "🚀 AI reasoning completed"
)
