import os
import requests

from dotenv import load_dotenv


# =========================
# LOAD WALLET
# =========================

load_dotenv(dotenv_path=".env")

wallet_address = os.getenv(
    "HL_ACCOUNT_ADDRESS"
)

if not wallet_address:
    raise RuntimeError(
        "HL_ACCOUNT_ADDRESS not configured"
    )


HL_INFO_URL = "https://api.hyperliquid.xyz/info"


def post_info(payload):

    response = requests.post(
        HL_INFO_URL,
        json=payload,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


# =========================
# SPOT BALANCE
# =========================

spot_data = post_info(
    {
        "type": "spotClearinghouseState",
        "user": wallet_address
    }
)


usdc_balance = 0.0

for balance in spot_data.get(
    "balances",
    []
):

    if balance.get("coin") == "USDC":

        usdc_balance = float(
            balance.get("total", 0)
        )


# =========================
# PERPS ACCOUNT
# =========================

perps_data = post_info(
    {
        "type": "clearinghouseState",
        "user": wallet_address
    }
)


perps_equity = float(
    perps_data["marginSummary"]["accountValue"]
)

withdrawable_perps = float(
    perps_data["withdrawable"]
)


# =========================
# OPEN ORDERS
# =========================

orders_data = post_info(
    {
        "type": "openOrders",
        "user": wallet_address
    }
)


# =========================
# OUTPUT
# =========================

print("\n")
print(
    "👁️ ACCOUNT VISIBILITY"
)

print("=" * 50)

print("\nWallet:")
print(wallet_address)


print("\nSPOT BALANCE")
print(
    f"USDC: {usdc_balance}"
)


print("\nPERPS ACCOUNT")

print(
    f"Equity: {perps_equity}"
)

print(
    f"Withdrawable: {withdrawable_perps}"
)

print(
    f"Open Positions: "
    f"{len(perps_data.get('assetPositions', []))}"
)


print("\nOPEN ORDERS")

print(
    len(orders_data)
)


print("\nTOTAL ACCOUNT VALUE")

print(
    f"USDC: {usdc_balance + perps_equity}"
)


print("\n✅ Account visibility completed")
