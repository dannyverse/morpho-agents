import requests
from datetime import datetime

market_cache = {}

last_update_timestamp = None


def refresh_market_data():

    global market_cache
    global last_update_timestamp

    try:

        response = requests.post(
            "https://api.hyperliquid.xyz/info",
            json={
                "type": "allMids"
            },
            timeout=5
        )

        market_cache = response.json()

        last_update_timestamp = str(
            datetime.now()
        )

        print("✅ Market data refreshed")

    except Exception as e:

        print(
            f"⚠️ Market data refresh error: {e}"
        )


def get_price(asset):

    return float(
        market_cache.get(asset, 0)
    )
