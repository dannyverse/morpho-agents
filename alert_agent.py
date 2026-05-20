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
# TRUSTED PROTOCOLS
# =========================

trusted_protocols = [
    "morpho-blue",
    "aave-v3",
    "spark",
    "compound-v3"
]

# =========================
# LOAD LIVE DATA
# =========================

url = "https://yields.llama.fi/pools"

response = requests.get(url)

data = response.json()["data"]

df = pd.DataFrame(data)

# =========================
# FILTER ETHEREUM ONLY
# =========================

stable = df[
    (df["stablecoin"] == True) &
    (df["chain"] == "Ethereum") &
    (df["project"].isin(trusted_protocols)) &
    (df["apy"] > 2) &
    (df["apy"] < 15) &
    (df["tvlUsd"] > 10_000_000)
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

        # EXISTING POSITION
        if not same.empty:

            old_apy = same.iloc[0]["apy"]

            diff = row["apy"] - old_apy

            if diff > 0.5:

                alerts.append(
                    f"🚀 APY UPGRADE\n\n"
                    f"Protocol: {row['project']}\n"
                    f"Asset: {row['symbol']}\n"
                    f"Old APY: {round(old_apy,2)}%\n"
                    f"New APY: {round(row['apy'],2)}%"
                )

            if diff < -0.5:

                alerts.append(
                    f"⚠️ APY DROP\n\n"
                    f"Protocol: {row['project']}\n"
                    f"Asset: {row['symbol']}\n"
                    f"Old APY: {round(old_apy,2)}%\n"
                    f"New APY: {round(row['apy'],2)}%"
                )

        # NEW OPPORTUNITY
        else:

            alerts.append(
                f"🔥 NEW OPPORTUNITY\n\n"
                f"Protocol: {row['project']}\n"
                f"Asset: {row['symbol']}\n"
                f"Chain: Ethereum\n"
                f"APY: {round(row['apy'],2)}%\n"
                f"TVL: ${round(row['tvlUsd']/1_000_000,2)}M"
            )

# =========================
# SEND ALERTS
# =========================

if len(alerts) == 0:

    send_telegram("✅ No important Ethereum stable yield changes")

else:

    for alert in alerts:

        send_telegram(alert)

# =========================
# SAVE SNAPSHOT
# =========================

stable.to_csv(snapshot_file, index=False)

print("Smart alerts completed")