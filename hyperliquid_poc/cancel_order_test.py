from hyperliquid.exchange import Exchange

from hyperliquid_poc.config import (
    API_WALLET,
    ACCOUNT_ADDRESS,
)

exchange = Exchange(
    wallet=API_WALLET,
    account_address=ACCOUNT_ADDRESS,
)

print("Cancelling Stop Loss...")

result = exchange.cancel(
    name="BTC",
    oid=496826875402,
)

print(result)
