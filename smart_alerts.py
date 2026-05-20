import requests
import pandas as pd
from dotenv import load_dotenv
import os

# =========================
# LOAD ENV
# =========================

load_dotenv(dotenv_path=".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# TELEGRAM FUNCTION
# =========================

def send_telegram(message):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)

# =========================
# LOAD LIVE DATA
# =========================

url = "https://yields.llama.fi/pools"

response = requests.get(url)

data = response.json()["data"]

df = pd.DataFrame(data)

# =========================
# FILTER GOOD STABLES
# =========================

stable = df[
    (df["stablecoin"] == True) &
    (df["apy"] > 3) &
    (df["tvlUsd"] > 1_000_000)
]

stable = stable[
    [
        "project",
        "symbol",
        "chain",
        "apy",
        "tvlUsd"
    ]
]

stable = stable.sort_values(
    by=["apy", "tvlUsd"],
    ascending=[False, False]
)

# =========================
# LOAD OLD SNAPSHOT
# =========================

snapshot_file = "yield_history.csv"

if os.path.exists(snapshot_file):

    old = pd.read_csv(snapshot_file)

else:

    old = pd.DataFrame()

# =========================
# COMPARE DATA
# =========================

alerts = []

if not old.empty:

    for _, row in stable.iterrows():

        same = old[
            (old["project"] == row["project"]) &
            (old["symbol"] == row["symbol"]) &
            (old["chain"] == row["chain"])
        ]

        if not same.empty:

            old_apy = same.iloc[0]["apy"]

            diff = row["apy"] - old_apy

            if diff > 1:

                alerts.append(
                    f"🚀 {row['project']} {row['symbol']} APY increased from {round(old_apy,2)}% to {round(row['apy'],2)}%"
                )

            if diff < -1:

                alerts.append(
                    f"⚠️ {row['project']} {row['symbol']} APY dropped from {round(old_apy,2)}% to {round(row['apy'],2)}%"
                )

# =========================
# SEND ALERTS
# =========================

if len(alerts) == 0:

    send_telegram("✅ No major APY changes detected")

else:

    for alert in alerts:

        send_telegram(alert)

# =========================
# SAVE NEW SNAPSHOT
# =========================

stable.to_csv(snapshot_file, index=False)

print("Smart alerts completed")