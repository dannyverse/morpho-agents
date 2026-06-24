import json
import requests

# =========================
# LOAD WALLET
# =========================

with open(
    "morpho_wallet.json",
    "r"
) as file:

    wallet_config = json.load(
        file
    )

wallet_address = (
    wallet_config[
        "wallet_address"
    ]
)

# =========================
# ACCOUNT STATE
# =========================

account_response = requests.post(
    "https://api.hyperliquid.xyz/info",
    json={
        "type": "clearinghouseState",
        "user": wallet_address
    },
    timeout=10
)

account_data = (
    account_response.json()
)

# =========================
# OPEN ORDERS
# =========================

orders_response = requests.post(
    "https://api.hyperliquid.xyz/info",
    json={
        "type": "openOrders",
        "user": wallet_address
    },
    timeout=10
)

orders_data = (
    orders_response.json()
)

# =========================
# OUTPUT
# =========================

print("\n")
print(
    "👁️ ACCOUNT VISIBILITY"
)

print("=" * 50)

print("\n")
print(
    f"Wallet: {wallet_address}"
)

print("\n")
print(
    f"Account Value: "
    f"{account_data['marginSummary']['accountValue']}"
)

print(
    f"Withdrawable: "
    f"{account_data['withdrawable']}"
)

print("\n")
print(
    f"Open Positions: "
    f"{len(account_data['assetPositions'])}"
)

print(
    f"Open Orders: "
    f"{len(orders_data)}"
)

print("\n")
print(
    "✅ Account visibility completed"
)
