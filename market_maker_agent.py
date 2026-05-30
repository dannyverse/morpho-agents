import requests
import pandas as pd
from datetime import datetime

# =========================
# API
# =========================

url = "https://api.hyperliquid.xyz/info"

payload = {

    "type": "metaAndAssetCtxs"
}

response = requests.post(

    url,

    json=payload
)

data = response.json()

assets = data[0]["universe"]

metrics = data[1]

# =========================
# ANALYSIS
# =========================

signals = []

for asset, metric in zip(

    assets,

    metrics
):

    try:

        funding = float(

            metric.get(
                "funding",
                0
            )
        )

        volume = float(

            metric.get(
                "dayNtlVlm",
                0
            )
        )

        mark_price = float(

            metric.get(
                "markPx",
                0
            )
        )

    except:

        continue

    signal = None

    rationale = None

    # =========================
    # FUNDING EXTREMES
    # =========================

    if funding > 0.0005:

        signal = "SHORT_BIAS"

        rationale = (
            "crowded_longs"
        )

    elif funding < -0.0005:

        signal = "LONG_BIAS"

        rationale = (
            "crowded_shorts"
        )

    # =========================
    # HIGH VOLUME TRAP
    # =========================

    if volume > 50000000:

        if signal is None:

            signal = "WATCH"

            rationale = (
                "high_activity"
            )

    # =========================
    # SAVE
    # =========================

    row = {

        "timestamp": str(
            datetime.now()
        ),

        "asset": asset["name"],

        "funding": funding,

        "volume": volume,

        "price": mark_price,

        "signal": signal,

        "rationale": rationale
    }

    signals.append(
        row
    )

# =========================
# DATAFRAME
# =========================

df = pd.DataFrame(
    signals
)

# =========================
# FILTER SIGNALS
# =========================

signal_df = df[

    df["signal"].notna()

]

# =========================
# OUTPUT
# =========================

print("\n")
print("=" * 60)

print(
    "🧠 MARKET MAKER INTELLIGENCE"
)

print("=" * 60)

print("\n")

print(

    signal_df.sort_values(

        "volume",

        ascending=False
    ).head(20)
)

print("\n")
print(
    "🚀 Market maker agent completed"
)