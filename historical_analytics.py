import sqlite3
import pandas as pd
import streamlit as st

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(

    page_title="Historical Analytics",

    layout="wide"
)

st.title(
    "📊 Autonomous Quant Intelligence"
)

# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

# =========================
# LOAD TABLES
# =========================

system_log = pd.read_sql_query(

    "SELECT * FROM system_log",

    conn
)

executions = pd.read_sql_query(

    "SELECT * FROM executions",

    conn
)

portfolio = pd.read_sql_query(

    "SELECT * FROM portfolio_state",

    conn
)

paper = pd.read_sql_query(

    "SELECT * FROM paper_portfolio",

    conn
)

conn.close()

# =========================
# EMPTY CHECKS
# =========================

if len(system_log) == 0:

    st.warning(
        "No historical logs yet"
    )

    st.stop()

# =========================
# KPI METRICS
# =========================

latest_equity = round(

    paper[
        "equity"
    ].iloc[-1],

    2
)

latest_exposure = round(

    paper[
        "exposure"
    ].iloc[-1],

    2
)

avg_health = round(

    system_log[
        "health_score"
    ].mean(),

    2
)

total_executions = len(
    executions
)

# =========================
# KPI ROW
# =========================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "💰 Equity",
    f"${latest_equity}"
)

col2.metric(
    "⚠️ Exposure",
    f"{latest_exposure}%"
)

col3.metric(
    "🧠 Avg Health",
    avg_health
)

col4.metric(
    "🚀 Executions",
    total_executions
)

# =========================
# EQUITY HISTORY
# =========================

st.subheader(
    "📈 Equity Evolution"
)

st.line_chart(
    paper["equity"]
)

# =========================
# EXPOSURE HISTORY
# =========================

st.subheader(
    "⚠️ Exposure Evolution"
)

st.line_chart(
    paper["exposure"]
)

# =========================
# HEALTH HISTORY
# =========================

st.subheader(
    "🧠 Health Score Evolution"
)

st.line_chart(
    system_log["health_score"]
)

# =========================
# EXECUTION DECISIONS
# =========================

st.subheader(
    "🚀 Execution Decisions"
)

decision_counts = executions[
    "execution_decision"
].value_counts()

st.bar_chart(
    decision_counts
)

# =========================
# REJECTION REASONS
# =========================

st.subheader(
    "❌ Rejection Reasons"
)

rejections = executions[

    executions[
        "execution_decision"
    ] == "REJECTED"

]

if len(rejections) > 0:

    rejection_counts = rejections[
        "rejection_reason"
    ].value_counts()

    st.bar_chart(
        rejection_counts
    )

# =========================
# RATIONALE BREAKDOWN
# =========================

st.subheader(
    "🧠 Trade Rationales"
)

rationale_counts = executions[
    "rationale"
].value_counts()

st.bar_chart(
    rationale_counts
)

# =========================
# REGIME DISTRIBUTION
# =========================

st.subheader(
    "🌍 Market Regimes"
)

regime_counts = executions[
    "regime"
].value_counts()

st.bar_chart(
    regime_counts
)

# =========================
# GOVERNANCE STATUS
# =========================

st.subheader(
    "🛡️ Governance Status"
)

governance_counts = executions[
    "governance_status"
].value_counts()

st.bar_chart(
    governance_counts
)

# =========================
# CONFIDENCE DISTRIBUTION
# =========================

st.subheader(
    "🎯 Confidence Distribution"
)

st.line_chart(
    executions[
        "confidence"
    ]
)

# =========================
# SIGNAL STRENGTH
# =========================

st.subheader(
    "⚡ Signal Strength"
)

st.line_chart(
    executions[
        "signal_strength"
    ]
)

# =========================
# REALIZED PNL
# =========================

closed_positions = portfolio[

    portfolio[
        "status"
    ] == "CLOSED"

]

if len(closed_positions) > 0:

    st.subheader(
        "💵 Realized PnL"
    )

    st.line_chart(

        closed_positions[
            "realized_pnl"
        ]
    )

# =========================
# RECENT EXECUTIONS
# =========================

st.subheader(
    "📂 Recent Executions"
)

st.dataframe(

    executions.tail(20)
)

# =========================
# RECENT PORTFOLIO
# =========================

st.subheader(
    "📂 Portfolio State"
)

st.dataframe(

    portfolio.tail(20)
)

# =========================
# STATUS
# =========================

st.success(
    "Autonomous intelligence active"
)