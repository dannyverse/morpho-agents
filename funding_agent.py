import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

# =========================
# LOAD ENV VARIABLES
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# TELEGRAM FUNCTION
# =========================

def send_telegram(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, json=payload)

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

# =========================
# SORT TOP FUNDING
# =========================

df["abs_funding"] = df["funding_apr"].abs()

top_df = df.sort_values(
    by="abs_funding",
    ascending=False
)

# =========================
# BUILD TELEGRAM MESSAGE
# =========================

message = "⚡ QUALITY FUNDING SIGNALS\n\n"

for _, row in top_df.head(5).iterrows():

    direction = (
        "LONGS PAYING"
        if row["funding_apr"] > 0
        else "SHORTS PAYING"
    )

    message += (
        f"🪙 {row['asset']}\n"
        f"📈 APR: {round(row['funding_apr'],2)}%\n"
        f"📊 {direction}\n"
        f"💰 OI: ${round(row['open_interest']/1_000_000,2)}M\n"
        f"🔄 Volume: ${round(row['volume']/1_000_000,2)}M\n\n"
    )

# =========================
# SEND TELEGRAM
# =========================

send_telegram(message)

print("Quality funding snapshot saved")