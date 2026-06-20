import json
import sqlite3
import pandas as pd
from market_data_manager import (
    refresh_market_data,
    get_market_cache
)

# ============================
# LOAD POSITION STATE
# ============================

conn = sqlite3.connect(
    "trading_system.db"
)

position_df = pd.read_sql(
    """
    SELECT *
    FROM portfolio_state
    WHERE status='OPEN'
    """,
    conn
)

conn.close()

# ============================
# LOAD MARKET DATA
# ============================

refresh_market_data()

market_data = get_market_cache()

# ============================
# MARK-TO-MARKET VALUATION
# ============================

for _, position in position_df.iterrows():

    asset = position["asset"]

    entry_price = position["entry_price"]

    quantity = position["position_size"]

    side = position["direction"]

    current_price = float(
        market_data.get(
            asset,
            0
        )
    )


    if side == "LONG":

        unrealized_pnl = (
            current_price - entry_price
        ) * quantity

    else:

        unrealized_pnl = (
            entry_price - current_price
        ) * quantity

    position["current_price"] = round(
        current_price,
        6
    )

    position["unrealized_pnl"] = round(
        unrealized_pnl,
        4
    )


# ============================
# OUTPUT
# ============================

print(
    "\n💰 POSITION VALUATOR\n"
)

print(
    position_df
)
