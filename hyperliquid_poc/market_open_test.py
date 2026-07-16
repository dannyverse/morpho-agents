from hyperliquid.exchange import Exchange

from hyperliquid_poc.config import (
    API_WALLET,
    ACCOUNT_ADDRESS,
)

exchange = Exchange(
    wallet=API_WALLET,
    account_address=ACCOUNT_ADDRESS,
)

print("Opening BTC market position...")

result = exchange.market_open(
    name="BTC",
    is_buy=True,
    sz=0.00017,
)

print(result)
