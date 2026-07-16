from hyperliquid.exchange import Exchange

from hyperliquid_poc.config import (
    API_WALLET,
    ACCOUNT_ADDRESS,
)

exchange = Exchange(
    wallet=API_WALLET,
    account_address=ACCOUNT_ADDRESS,
)

print("Placing native Take Profit...")

result = exchange.order(
    name="BTC",
    is_buy=False,
    sz=0.00017,
    limit_px=66000.0,
    reduce_only=True,
    order_type={
        "trigger": {
            "triggerPx": 66000.0,
            "isMarket": True,
            "tpsl": "tp",
        }
    },
)

print(result)
