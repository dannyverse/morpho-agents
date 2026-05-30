import sqlite3
import pandas as pd

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
# LOAD SIGNAL MEMORY
# =========================

signal_query = """

SELECT *

FROM signal_memory

"""

signal_df = pd.read_sql_query(
    signal_query,
    conn
)

conn.close()

# =========================
# CLEAN
# =========================

portfolio_df = portfolio_df.dropna()

signal_df = signal_df.dropna()

# =========================
# RECENT SIGNALS
# =========================

recent = signal_df.tail(20)

wins = len(

    recent[
        recent["pnl"] > 0
    ]
)

losses = len(

    recent[
        recent["pnl"] <= 0
    ]
)

# =========================
# WINRATE
# =========================

winrate = round(

    (wins / len(recent)) * 100,
    2
)

# =========================
# AVG PNL
# =========================

avg_pnl = round(

    recent[
        "pnl"
    ].mean(),
    2
)

# =========================
# VOLATILITY
# =========================

volatility = round(

    recent[
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

        avg_pnl / volatility,
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
        (current_equity - max_equity)

        / max_equity
    ) * 100,

    2
)

# =========================
# HEALTH SCORE
# =========================

health_score = 100

health_score += avg_pnl * 2

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

if drawdown < -10:

    system_status = "RISK"

if sharpe_like < 0:

    system_status = "UNSTABLE"

if health_score < 80:

    system_status = "WARNING"

# =========================
# OUTPUT
# =========================

print("\n")
print("🧠 PORTFOLIO HEALTH")
print("=" * 40)

print(
    f"\nWinrate: "
    f"{winrate}%"
)

print(
    f"Average PnL: "
    f"{avg_pnl}%"
)

print(
    f"Volatility: "
    f"{volatility}"
)

print(
    f"Sharpe-Like: "
    f"{sharpe_like}"
)

print(
    f"Drawdown: "
    f"{drawdown}%"
)

print(
    f"Health Score: "
    f"{health_score}"
)

print(
    f"System Status: "
    f"{system_status}"
)

print("\n")
print("🚀 Portfolio health completed")