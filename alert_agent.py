import requests
import pandas as pd
import os
from notifier import notify

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

                alerts.append({
                    "level": "INFO",
                    "title": (
                        f"OPPORTUNITY · APY UPGRADE · "
                        f"{row['project']} · {row['symbol']}"
                    ),
                    "body": (
                        "The monitored APY increased beyond the "
                        "configured change threshold."
                    ),
                    "details": {
                        "Protocol": row["project"],
                        "Asset": row["symbol"],
                        "Previous APY": f"{round(old_apy, 2)}%",
                        "Current APY": f"{round(row['apy'], 2)}%",
                    },
                })

            if diff < -0.5:

                alerts.append({
                    "level": "WARNING",
                    "title": (
                        f"OPPORTUNITY · APY DROP · "
                        f"{row['project']} · {row['symbol']}"
                    ),
                    "body": (
                        "The monitored APY decreased beyond the "
                        "configured change threshold."
                    ),
                    "details": {
                        "Protocol": row["project"],
                        "Asset": row["symbol"],
                        "Previous APY": f"{round(old_apy, 2)}%",
                        "Current APY": f"{round(row['apy'], 2)}%",
                    },
                })

        # NEW OPPORTUNITY
        else:

            alerts.append({
                "level": "INFO",
                "title": (
                    f"OPPORTUNITY · NEW YIELD · "
                    f"{row['project']} · {row['symbol']}"
                ),
                "body": (
                    "A new yield opportunity passed the configured "
                    "monitoring filters."
                ),
                "details": {
                    "Protocol": row["project"],
                    "Asset": row["symbol"],
                    "Chain": "Ethereum",
                    "APY": f"{round(row['apy'], 2)}%",
                    "TVL": f"${round(row['tvlUsd'] / 1_000_000, 2)}M",
                },
            })

# =========================
# SEND ALERTS
# =========================

if len(alerts) == 0:

    notify(
        level="INFO",
        title="OPPORTUNITY · YIELD MONITOR STATUS",
        body="No important Ethereum stable-yield changes were detected."
    )

else:

    for alert in alerts:

        notify(
            level=alert["level"],
            title=alert["title"],
            body=alert["body"],
            details=alert["details"]
        )

# =========================
# SAVE SNAPSHOT
# =========================

stable.to_csv(snapshot_file, index=False)

print("Smart alerts completed")
