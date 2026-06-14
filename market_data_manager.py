import requests
from datetime import datetime
from datetime import timezone
from telemetry import log_market_event
market_cache = {}

last_update_timestamp = None
market_data_age_seconds = None
WARNING_THRESHOLD_SECONDS = 120

CRITICAL_THRESHOLD_SECONDS = 300
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

        log_market_event(
            event="market_data_refreshed",
            status=get_market_data_status(),
            details={
                "assets_loaded": len(market_cache)
            }
        )        

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
def is_market_data_stale():

    age = get_market_data_age()

    if age is None:
        return True

    return age > WARNING_THRESHOLD_SECONDS

    
def get_market_data_status():

    age = get_market_data_age()

    if age is None:
        return "UNKNOWN"

    if age > CRITICAL_THRESHOLD_SECONDS:
        return "CRITICAL"

    if age > WARNING_THRESHOLD_SECONDS:
        return "WARNING"

    return "HEALTHY"
    
        

    
