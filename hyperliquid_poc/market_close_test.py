from hyperliquid.exchange import Exchange

from hyperliquid_poc.config import (
    API_WALLET,
    ACCOUNT_ADDRESS,
)

exchange = Exchange(
    wallet=API_WALLET,
    account_address=ACCOUNT_ADDRESS,
)

print("Closing BTC position...")

result = exchange.market_close(
    coin="BTC",
)

print(result)
