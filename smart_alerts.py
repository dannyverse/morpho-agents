import pandas as pd
import requests
import os
from notifier import notify


# =========================
# CONFIG
# =========================

TRUSTED_PROTOCOLS = [
    "aave",
    "morpho",
    "spark",
    "compound"
]

STABLES = [
    "USDC",
    "USDT",
    "DAI",
    "USDS",
    "SUSDS",
    "USR",
    "RLUSD"
]

HISTORY_FILE = "yield_history.csv"


# =========================
# FETCH DATA
# =========================

url = "https://yields.llama.fi/pools"

data = requests.get(url).json()

df = pd.DataFrame(data["data"])


# =========================
# FILTERS
# =========================

filtered_rows = []

for _, row in df.iterrows():

    project = str(row.get("project", "")).lower()

    if project not in TRUSTED_PROTOCOLS:
        continue

    chain = str(row.get("chain", "")).lower()

    if chain != "ethereum":
        continue

    symbol = str(row.get("symbol", "")).upper()

    if symbol not in STABLES:
        continue

    apy = row.get("apy")

    if apy is None:
        continue

    # Ignorar APYs absurdos
    if apy < 3 or apy > 20:
        continue

    filtered_rows.append({
        "project": project,
        "symbol": symbol,
        "apy": apy
    })

new_df = pd.DataFrame(filtered_rows)


# =========================
# FIRST RUN
# =========================

if not os.path.exists(HISTORY_FILE):

    new_df.to_csv(HISTORY_FILE, index=False)

    notify(
        level="INFO",
        title="OPPORTUNITY · YIELD MONITOR INITIALIZED",
        body="The initial yield snapshot was created successfully."
    )

    print("First snapshot created")

    exit()


# =========================
# LOAD OLD SNAPSHOT
# =========================

old_df = pd.read_csv(HISTORY_FILE)


# =========================
# COMPARE
# =========================

for _, row in new_df.iterrows():

    project = row["project"]
    symbol = row["symbol"]
    new_apy = row["apy"]

    match = old_df[
        (old_df["project"] == project) &
        (old_df["symbol"] == symbol)
    ]

    if match.empty:
        continue

    old_apy = match.iloc[0]["apy"]

    change = abs(new_apy - old_apy)

    # Ignorar cambios pequeños
    if change < 1.0:
        continue

    # Ignorar APYs bajos
    if new_apy < 6:
        continue

    direction = "increased" if new_apy > old_apy else "dropped"

    message = "The monitored APY changed beyond the configured threshold."

    notify(
        level="WARNING",
        title=f"OPPORTUNITY · APY CHANGE · {project} · {symbol}",
        body=message,
        details={
            "Protocol": project,
            "Asset": symbol,
            "Direction": direction,
            "Previous APY": f"{round(old_apy, 2)}%",
            "Current APY": f"{round(new_apy, 2)}%",
        }
    )

    print(message)


# =========================
# SAVE NEW SNAPSHOT
# =========================

new_df.to_csv(HISTORY_FILE, index=False)

print("Smart alerts completed")
