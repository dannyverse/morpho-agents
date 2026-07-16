from hyperliquid.exchange import Exchange

from hyperliquid_poc.config import (
    API_WALLET,
    ACCOUNT_ADDRESS,
)

exchange = Exchange(
    wallet=API_WALLET,
    account_address=ACCOUNT_ADDRESS,
)

print("Placing native Stop Loss...")

result = exchange.order(
    name="BTC",
    is_buy=False,          # Cierra una posición LONG
    sz=0.00017,
    limit_px=64000.0,      # Debe existir, aunque sea trigger market
    reduce_only=True,
    order_type={
        "trigger": {
            "triggerPx": 64000.0,
            "isMarket": True,
            "tpsl": "sl",
        }
    },
)

print(result)
