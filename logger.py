import sqlite3
import pandas as pd
from datetime import datetime
import os

# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

# =========================
# CREATE TABLE
# =========================

create_query = """

CREATE TABLE IF NOT EXISTS
system_log (

    timestamp TEXT,

    market_regime TEXT,

    equity REAL,

    exposure REAL,

    open_positions INTEGER,

    health_score REAL,

    system_status TEXT
)

"""

conn.execute(
    create_query
)

# =========================
# SAFE LOAD PORTFOLIO
# =========================

try:

    portfolio_query = """

    SELECT *

    FROM paper_portfolio

    ORDER BY ROWID DESC

    LIMIT 1

    """

    portfolio_df = pd.read_sql_query(
        portfolio_query,
        conn
    )

except:

    portfolio_df = pd.DataFrame()

# =========================
# SAFE LOAD POSITIONS
# =========================

try:

    positions_query = """

    SELECT *

    FROM portfolio_state

    WHERE status='OPEN'

    """

    positions_df = pd.read_sql_query(
        positions_query,
        conn
    )

except:

    positions_df = pd.DataFrame()

# =========================
# MARKET REGIME
# =========================

market_regime = "NEUTRAL"

if os.path.exists(
    "market_regime.txt"
):

    with open(
        "market_regime.txt",
        "r"
    ) as f:

        market_regime = (
            f.read().strip()
        )

# =========================
# SAFE METRICS
# =========================

equity = 0

exposure = 0

open_positions = 0

avg_pnl = 0

volatility = 0

# =========================
# EQUITY
# =========================

if (

    len(portfolio_df) > 0

    and

    "equity" in portfolio_df.columns
):

    equity = round(

        portfolio_df[
            "equity"
        ].iloc[-1],

        2
    )

# =========================
# EXPOSURE
# =========================

if (

    len(portfolio_df) > 0

    and

    "exposure" in portfolio_df.columns
):

    exposure = round(

        portfolio_df[
            "exposure"
        ].iloc[-1],

        2
    )

# =========================
# OPEN POSITIONS
# =========================

open_positions = len(
    positions_df
)

# =========================
# PNL METRICS
# =========================

if (

    len(positions_df) > 0

    and

    "unrealized_pnl"

    in positions_df.columns
):

    avg_pnl = round(

        positions_df[
            "unrealized_pnl"
        ].mean(),

        2
    )

    volatility = round(

        positions_df[
            "unrealized_pnl"
        ].std(),

        2
    )

# =========================
# HEALTH SCORE
# =========================

health_score = 100

health_score += avg_pnl * 2

if volatility > 0:

    health_score += (

        avg_pnl /

        volatility

    ) * 10

health_score = round(
    health_score,
    2
)

# =========================
# SYSTEM STATUS
# =========================

system_status = "HEALTHY"

if health_score < 90:

    system_status = "WARNING"

if health_score < 75:

    system_status = "RISK"

# =========================
# BUILD LOG ENTRY
# =========================

log_entry = {

    "timestamp": str(
        datetime.now()
    ),

    "market_regime": market_regime,

    "equity": equity,

    "exposure": exposure,

    "open_positions": open_positions,

    "health_score": health_score,

    "system_status": system_status
}

log_df = pd.DataFrame(
    [log_entry]
)

# =========================
# SAVE
# =========================

log_df.to_sql(

    "system_log",

    conn,

    if_exists="append",

    index=False
)

conn.close()

# =========================
# OUTPUT
# =========================

print("\n")
print("🧠 SYSTEM LOGGER")

print(
    f"\nHealth Score: "
    f"{health_score}"
)

print(
    f"System Status: "
    f"{system_status}"
)

print("\n")
print(
    "🚀 Logger completed"
)