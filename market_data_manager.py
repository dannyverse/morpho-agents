import requests
from datetime import datetime
from datetime import timezone
market_cache = {}

last_update_timestamp = None
market_data_age_seconds = None

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

        last_update_timestamp = datetime.now(
            timezone.utc
        )
        
        market_data_age_seconds = 0
            
        

        print("✅ Market data refreshed")

    except Exception as e:

        print(
            f"⚠️ Market data refresh error: {e}"
        )


def get_price(asset):

    return float(
        market_cache.get(asset, 0)
    )

def get_market_data_age():

    global last_update_timestamp

    if not last_update_timestamp:
        return None

    return round(
        (
            datetime.now(timezone.utc)
            - last_update_timestamp
        ).total_seconds(),
        2
    )
