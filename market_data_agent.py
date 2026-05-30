import requests
import pandas as pd
from datetime import datetime

# =========================
# HYPERLIQUID API
# =========================

url = "https://api.hyperliquid.xyz/info"

payload = {

    "type": "metaAndAssetCtxs"
}

# =========================
# REQUEST
# =========================

response = requests.post(

    url,

    json=payload
)

data = response.json()

# =========================
# PARSE ASSETS
# =========================

assets = data[0]["universe"]

metrics = data[1]

rows = []

for asset, metric in zip(

    assets,

    metrics
):

    row = {

        "timestamp": str(
            datetime.now()
        ),

        "asset": asset["name"],

        "funding": metric.get(
            "funding",
            None
        ),

        "open_interest": metric.get(
            "openInterest",
            None
        ),

        "mark_price": metric.get(
            "markPx",
            None
        ),

        "volume_24h": metric.get(
            "dayNtlVlm",
            None
        )
    }

    rows.append(
        row
    )

# =========================
# DATAFRAME
# =========================

df = pd.DataFrame(
    rows
)

# =========================
# SORT
# =========================

df = df.sort_values(

    "volume_24h",

    ascending=False
)

# =========================
# OUTPUT
# =========================

print("\n")
print("=" * 60)

print(
    "🚀 HYPERLIQUID MARKET DATA"
)

print("=" * 60)

print("\n")

print(

    df.head(20)
)

print("\n")
print(
    "✅ Market data agent completed"
)