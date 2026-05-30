import streamlit as st
import sqlite3
import pandas as pd
import time

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(

    page_title="Autonomous Quant Intelligence",

    layout="wide"
)

# =========================
# AUTO REFRESH
# =========================

time.sleep(1)

# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

# =========================
# LOAD DATA
# =========================

executions_query = """

SELECT *

FROM executions

ORDER BY ROWID DESC

LIMIT 50

"""

portfolio_query = """

SELECT *

FROM paper_portfolio

ORDER BY ROWID DESC

LIMIT 50

"""

positions_query = """

SELECT *

FROM position_state

ORDER BY position_pnl DESC

LIMIT 20

"""

executions = pd.read_sql_query(

    executions_query,

    conn
)

portfolio = pd.read_sql_query(

    portfolio_query,

    conn
)

positions = pd.read_sql_query(

    positions_query,

    conn
)

conn.close()

# =========================
# HEADER
# =========================

st.title(
    "🚀 Autonomous Quant Intelligence"
)

st.markdown("---")

# =========================
# PORTFOLIO METRICS
# =========================

if len(portfolio) > 0:

    latest = portfolio.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(

        "💼 Equity",

        f"${latest['equity']:.2f}"
    )

    col2.metric(

        "📈 Exposure",

        f"{latest['exposure']}%"
    )

    col3.metric(

        "⚔️ Open Positions",

        int(latest['open_positions'])
    )

    col4.metric(

        "🧠 Unrealized PnL",

        f"{latest['unrealized_pnl']:.2f}%"
    )

# =========================
# EQUITY CURVE
# =========================

st.markdown("---")

st.subheader(
    "📈 Portfolio Equity Curve"
)

if len(portfolio) > 0:

    equity_chart = portfolio.sort_values(
        "timestamp"
    )

    st.line_chart(

        equity_chart[
            "equity"
        ]
    )

# =========================
# EXECUTION FEED
# =========================

st.markdown("---")

left, right = st.columns(2)

with left:

    st.subheader(
        "⚔️ Recent Executions"
    )

    if len(executions) > 0:

        execution_view = executions[
            [
                "asset",
                "confidence",
                "signal_strength",
                "execution_decision",
                "rationale"
            ]
        ]

        st.dataframe(

            execution_view,

            use_container_width=True
        )

with right:

    st.subheader(
        "🏆 Top Positions"
    )

    if len(positions) > 0:

        position_view = positions[
            [
                "asset",
                "position_size",
                "position_pnl"
            ]
        ]

        st.dataframe(

            position_view,

            use_container_width=True
        )

# =========================
# RATIONALE ANALYTICS
# =========================

st.markdown("---")

st.subheader(
    "🧠 Rationale Distribution"
)

if len(executions) > 0:

    rationale_counts = executions[
        "rationale"
    ].value_counts()

    st.bar_chart(
        rationale_counts
    )

# =========================
# APPROVAL ANALYTICS
# =========================

st.markdown("---")

st.subheader(
    "✅ Approval vs Rejection"
)

if len(executions) > 0:

    approval_counts = executions[
        "execution_decision"
    ].value_counts()

    st.bar_chart(
        approval_counts
    )

# =========================
# FOOTER
# =========================

st.markdown("---")

st.success(
    "🚀 Autonomous Quant System Operational"
)