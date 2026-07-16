from hyperliquid.exchange import Exchange

from hyperliquid_poc.config import (
    API_WALLET,
    ACCOUNT_ADDRESS,
)

exchange = Exchange(
    wallet=API_WALLET,
    account_address=ACCOUNT_ADDRESS,
)

print("Transferring 10 USDC from Spot to Perps...")

result = exchange.usd_class_transfer(
    amount=10.0,
    to_perp=True,
)

print(result)
