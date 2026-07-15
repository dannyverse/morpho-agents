from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

from hyperliquid_poc.config import (
    API_WALLET,
    ACCOUNT_ADDRESS,
)

print("=" * 60)
print("MORPHO - Hyperliquid Authentication Test")
print("=" * 60)

info = Info(skip_ws=True)

state = info.user_state(ACCOUNT_ADDRESS)

print("\nConnected successfully.\n")

print(f"Account: {ACCOUNT_ADDRESS}")
print(f"Withdrawable: {state['withdrawable']}")

print("\nMargin Summary")
print(state["marginSummary"])

print("\nOpen Positions")
print(len(state["assetPositions"]))

exchange = Exchange(
    wallet=API_WALLET,
    account_address=ACCOUNT_ADDRESS,
)

print("\nExchange client created successfully.")

import json

print("\n===== RAW USER STATE =====\n")
print(json.dumps(state, indent=2))

print("\n===== SPOT USER STATE =====\n")
print(json.dumps(info.spot_user_state(ACCOUNT_ADDRESS), indent=2))
