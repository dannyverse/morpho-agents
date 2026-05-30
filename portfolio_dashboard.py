import sqlite3
import pandas as pd
import streamlit as st

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(

    page_title="Quant Dashboard",

    layout="wide"
)

st.title(
    "📈 Quant Portfolio Dashboard"
)

# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

# =========================
# LOAD PAPER PORTFOLIO
# =========================

portfolio_query = """

SELECT *

FROM paper_portfolio

"""

portfolio_df = pd.read_sql_query(

    portfolio_query,
    conn
)

# =========================
# LOAD SYSTEM LOG
# =========================

log_query = """

SELECT *

FROM system_log

"""

log_df = pd.read_sql_query(

    log_query,
    conn
)

# =========================
# LOAD POSITIONS
# =========================

positions_query = """

SELECT *

FROM portfolio_state

WHERE status='OPEN'

"""

positions_df = pd.read_sql_query(

    positions_query,
    conn
)

conn.close()

# =========================
# CLEAN DATA
# =========================

portfolio_df = portfolio_df.dropna()

log_df = log_df.dropna()

positions_df = positions_df.dropna()

# =========================
# BASIC METRICS
# =========================

latest_equity = round(

    portfolio_df[
        "equity"
    ].iloc[-1],

    2
)

latest_cash = round(

    portfolio_df[
        "cash"
    ].iloc[-1],

    2
)

latest_exposure = round(

    portfolio_df[
        "exposure"
    ].iloc[-1],

    2
)

latest_pnl = round(

    portfolio_df[
        "realized_pnl"
    ].iloc[-1],

    2
)

# =========================
# REGIME
# =========================

latest_regime = "NEUTRAL"

if len(log_df) > 0:

    latest_regime = (

        log_df[
            "market_regime"
        ].iloc[-1]
    )

# =========================
# EQUITY DELTA
# =========================

equity_delta = 0

if len(portfolio_df) > 1:

    equity_delta = round(

        portfolio_df[
            "equity"
        ].iloc[-1]

        -

        portfolio_df[
            "equity"
        ].iloc[-2],

        2
    )

# =========================
# DRAWDOWN
# =========================

max_equity = portfolio_df[
    "equity"
].max()

current_equity = portfolio_df[
    "equity"
].iloc[-1]

drawdown = round(

    (
        current_equity -

        max_equity
    )

    /

    max_equity

    * 100,

    2
)

# =========================
# LONG / SHORT
# =========================

long_positions = len(

    positions_df[
        positions_df[
            "direction"
        ] == "LONG"
    ]
)

short_positions = len(

    positions_df[
        positions_df[
            "direction"
        ] == "SHORT"
    ]
)

# =========================
# HEALTH METRICS
# =========================

recent_signals = positions_df.tail(20)

wins = len(

    recent_signals[
        recent_signals[
            "pnl"
        ] > 0
    ]
)

losses = len(

    recent_signals[
        recent_signals[
            "pnl"
        ] <= 0
    ]
)

# =========================
# WINRATE
# =========================

winrate = 0

if len(recent_signals) > 0:

    winrate = round(

        (
            wins /

            len(recent_signals)
        ) * 100,

        2
    )

# =========================
# AVG PNL
# =========================

avg_signal_pnl = round(

    recent_signals[
        "pnl"
    ].mean(),

    2
)

# =========================
# VOLATILITY
# =========================

volatility = round(

    recent_signals[
        "pnl"
    ].std(),

    2
)

# =========================
# SHARPE-LIKE
# =========================

sharpe_like = 0

if volatility > 0:

    sharpe_like = round(

        avg_signal_pnl /

        volatility,

        2
    )

# =========================
# HEALTH SCORE
# =========================

health_score = 100

health_score += avg_signal_pnl * 2

health_score += sharpe_like * 10

health_score -= abs(drawdown)

health_score = round(
    health_score,
    2
)

# =========================
# SYSTEM STATUS
# =========================

system_status = "HEALTHY"

if health_score < 80:

    system_status = "WARNING"

if sharpe_like < 0:

    system_status = "UNSTABLE"

if drawdown < -10:

    system_status = "RISK"

# =========================
# TOP METRICS
# =========================

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric(
    "💰 Equity",
    f"${latest_equity}"
)

col2.metric(
    "💵 Cash",
    f"${latest_cash}"
)

col3.metric(
    "⚠️ Exposure",
    f"{latest_exposure}%"
)

col4.metric(
    "📈 Realized PnL",
    f"{latest_pnl}%"
)

col5.metric(
    "📉 Drawdown",
    f"{drawdown}%"
)

col6.metric(
    "🧠 Health",
    f"{health_score}"
)

# =========================
# REGIME BADGE
# =========================

st.subheader(
    "🧠 Market Regime"
)

if latest_regime == "AGGRESSIVE":

    st.success(
        latest_regime
    )

elif latest_regime == "DEFENSIVE":

    st.error(
        latest_regime
    )

else:

    st.warning(
        latest_regime
    )

# =========================
# SYSTEM STATUS
# =========================

st.subheader(
    "🛡️ System Status"
)

if system_status == "HEALTHY":

    st.success(
        system_status
    )

elif system_status == "WARNING":

    st.warning(
        system_status
    )

else:

    st.error(
        system_status
    )

# =========================
# HEALTH METRICS
# =========================

health_col1, health_col2, health_col3 = st.columns(3)

health_col1.metric(
    "🎯 Winrate",
    f"{winrate}%"
)

health_col2.metric(
    "📊 Volatility",
    volatility
)

health_col3.metric(
    "⚡ Sharpe-Like",
    sharpe_like
)

# =========================
# EQUITY DELTA
# =========================

st.subheader(
    "💰 Equity Delta"
)

if equity_delta >= 0:

    st.success(
        f"+${equity_delta}"
    )

else:

    st.error(
        f"-${abs(equity_delta)}"
    )

# =========================
# PORTFOLIO COMPOSITION
# =========================

st.subheader(
    "⚖️ Portfolio Composition"
)

comp_col1, comp_col2 = st.columns(2)

comp_col1.metric(
    "LONG Positions",
    long_positions
)

comp_col2.metric(
    "SHORT Positions",
    short_positions
)

# =========================
# EQUITY CURVE
# =========================

st.subheader(
    "📈 Equity Curve"
)

st.line_chart(
    portfolio_df["equity"]
)

# =========================
# EXPOSURE HISTORY
# =========================

st.subheader(
    "⚠️ Exposure History"
)

st.line_chart(
    portfolio_df["exposure"]
)

# =========================
# PNL EVOLUTION
# =========================

st.subheader(
    "💹 Realized PnL"
)

st.line_chart(
    portfolio_df[
        "realized_pnl"
    ]
)

# =========================
# OPEN POSITIONS
# =========================

st.subheader(
    "📂 Open Positions"
)

st.dataframe(

    positions_df[
        [
            "asset",
            "direction",
            "position_size",
            "pnl"
        ]
    ].tail(20)
)

# =========================
# SYSTEM LOG
# =========================

st.subheader(
    "🧠 System Log"
)

st.dataframe(
    log_df.tail(20)
)

# =========================
# PORTFOLIO SNAPSHOTS
# =========================

st.subheader(
    "📋 Portfolio Snapshots"
)

st.dataframe(
    portfolio_df.tail(20)
)