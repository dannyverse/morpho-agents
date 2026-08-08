import requests
import pandas as pd
import os
from datetime import datetime

# =========================
# HYPERLIQUID API REQUEST
# =========================

url = "https://api.hyperliquid.xyz/info"

payload = {
    "type": "metaAndAssetCtxs"
}

response = requests.post(url, json=payload)

data = response.json()

meta = data[0]
contexts = data[1]

assets = meta["universe"]

# =========================
# BUILD DATASET
# =========================

rows = []

timestamp = datetime.utcnow()

for asset, ctx in zip(assets, contexts):

    try:

        name = asset["name"]

        funding = float(ctx.get("funding", 0))

        annualized = funding * 24 * 365 * 100

        open_interest = float(
            ctx.get("openInterest", 0)
        )

        volume = float(
            ctx.get("dayNtlVlm", 0)
        )

        # =========================
        # FILTER ENGINE
        # =========================

        # Ignore low liquidity
        if volume < 5_000_000:
            continue

        # Ignore low OI
        if open_interest < 2_000_000:
            continue

        # Ignore absurd spikes
        if abs(annualized) > 200:
            continue

        rows.append({
            "timestamp": timestamp,
            "asset": name,
            "funding_apr": annualized,
            "open_interest": open_interest,
            "volume": volume
        })

    except Exception as e:

        print("Error:", e)

# =========================
# CREATE DATAFRAME
# =========================

df = pd.DataFrame(rows)

if df.empty:

    print("No quality funding opportunities found")

    exit()

# =========================
# SAVE HISTORY CSV
# =========================

history_file = "funding_history.csv"

file_exists = os.path.exists(history_file)

file_empty = (
    not file_exists
    or os.path.getsize(history_file) == 0
)

df.to_csv(
    history_file,
    mode="a",
    header=file_empty,
    index=False
)

print("Quality funding snapshot saved")
