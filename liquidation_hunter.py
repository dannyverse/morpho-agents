import sqlite3
import requests
import pandas as pd

from datetime import datetime

from telegram_test import send_alert

# =========================
# HYPERLIQUID API
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
# DETECTION
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

        open_interest = float(

            metric.get(
                "openInterest",
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

    # =========================
    # DEFAULTS
    # =========================

    squeeze_risk = None

    commentary = None

    # =========================
    # LONG SQUEEZE
    # =========================

    if (

        funding > 0.0007

        and

        volume > 25000000
    ):

        squeeze_risk = "LONG_SQUEEZE"

        commentary = (

            "Crowded longs detected."
        )

    # =========================
    # SHORT SQUEEZE
    # =========================

    elif (

        funding < -0.0007

        and

        volume > 25000000
    ):

        squeeze_risk = "SHORT_SQUEEZE"

        commentary = (

            "Crowded shorts detected."
        )

    # =========================
    # BUILD SIGNAL
    # =========================

    signal = {

        "timestamp": str(
            datetime.now()
        ),

        "asset": asset["name"],

        "funding": funding,

        "volume": volume,

        "open_interest": open_interest,

        "price": mark_price,

        "squeeze_risk": squeeze_risk,

        "commentary": commentary
    }

    signals.append(
        signal
    )

# =========================
# DATAFRAME
# =========================

df = pd.DataFrame(
    signals
)

# =========================
# ACTIVE SIGNALS
# =========================

active_df = df[

    df[
        "squeeze_risk"
    ].notna()

]

# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

# =========================
# CREATE TABLE
# =========================

create_query = """

CREATE TABLE IF NOT EXISTS
liquidation_signals (

    timestamp TEXT,

    asset TEXT,

    funding REAL,

    volume REAL,

    open_interest REAL,

    price REAL,

    squeeze_risk TEXT,

    commentary TEXT
)

"""

conn.execute(
    create_query
)

# =========================
# SAVE
# =========================

active_df.to_sql(

    "liquidation_signals",

    conn,

    if_exists="append",

    index=False
)

conn.close()

# =========================
# TELEGRAM ALERTS
# =========================

for _, row in active_df.iterrows():

    telegram_message = (

        f"⚠️ LIQUIDATION HUNTER\n\n"

        f"Asset: {row['asset']}\n"

        f"Squeeze Risk: {row['squeeze_risk']}\n"

        f"Funding: {row['funding']}\n"

        f"Volume: {round(row['volume'], 2)}\n\n"

        f"{row['commentary']}"
    )

    send_alert(
        telegram_message
    )

# =========================
# OUTPUT
# =========================

print("\n")
print("=" * 60)

print(
    "🔥 LIQUIDATION HUNTER"
)

print("=" * 60)

print("\n")

print(
    active_df.head(20)
)

print("\n")
print(
    "🚀 Liquidation hunter completed"
)