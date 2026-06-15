import json
from market_data_manager import (
    refresh_market_data,
    get_market_cache
)

# ============================
# LOAD POSITION STATE
# ============================

with open(
    "state/position_state.json",
    "r"
) as f:

    position_state = json.load(f)


# ============================
# LOAD MARKET DATA
# ============================

refresh_market_data()

market_data = get_market_cache()

# ============================
# MARK-TO-MARKET VALUATION
# ============================

for asset, position in position_state.items():

    current_price = float(
        market_data.get(
            asset,
            0
        )
    )
    entry_price = position["entry_price"]

    quantity = position["quantity"]

    side = position["side"]

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
    json.dumps(
        position_state,
        indent=4
    )
)
