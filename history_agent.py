import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Yield History Agent", layout="wide")

st.title("📈 Yield History Agent")

url = "https://yields.llama.fi/pools"

response = requests.get(url)

data = response.json()["data"]

stable_keywords = [
    "USDC",
    "USDT",
    "DAI",
    "USDS",
    "RLUSD",
    "PYUSD"
]

trusted_protocols = [
    "morpho-blue",
    "aave-v3",
    "spark",
    "sky",
    "compound-v3",
    "curve",
    "fluid",
    "euler"
]

filtered_pools = []

for pool in data:

    symbol = str(pool.get("symbol", "")).upper()
    project = str(pool.get("project", "")).lower()

    if not any(keyword in symbol for keyword in stable_keywords):
        continue

    apy = pool.get("apy", 0)
    tvl = pool.get("tvlUsd", 0)

    if apy is None or tvl is None:
        continue

    if apy > 20:
        continue

    if apy < 1:
        continue

    if tvl < 5_000_000:
        continue

    risk = "Low"

    if apy > 8:
        risk = "High"

    elif apy > 5:
        risk = "Medium"

    trusted = project in trusted_protocols

    score = 100

    if risk == "Medium":
        score -= 15

    if risk == "High":
        score -= 35

    if not trusted:
        score -= 20

    if tvl < 20_000_000:
        score -= 10

    filtered_pools.append({
        "Project": project,
        "Symbol": symbol,
        "Chain": pool.get("chain", ""),
        "APY": round(apy, 2),
        "TVL": round(tvl, 0),
        "Risk": risk,
        "Score": score
    })

df = pd.DataFrame(filtered_pools)

df = df.sort_values(by="Score", ascending=False)

# =========================
# HISTORICAL STORAGE
# =========================

history_file = "yield_history.csv"

if os.path.exists(history_file):

    old_df = pd.read_csv(history_file)

    comparison = df.merge(
        old_df,
        on=["Project", "Symbol", "Chain"],
        how="left",
        suffixes=("", "_OLD")
    )

    comparison["APY Change"] = comparison["APY"] - comparison["APY_OLD"]

    comparison["TVL Change"] = comparison["TVL"] - comparison["TVL_OLD"]

else:

    comparison = df.copy()

    comparison["APY Change"] = 0
    comparison["TVL Change"] = 0

# save latest snapshot

df.to_csv(history_file, index=False)

# =========================
# DASHBOARD
# =========================

st.subheader("Top Stable Opportunities")

st.dataframe(
    comparison[
        [
            "Project",
            "Symbol",
            "Chain",
            "APY",
            "APY Change",
            "TVL",
            "TVL Change",
            "Risk",
            "Score"
        ]
    ].head(30),
    use_container_width=True
)

# alerts

st.subheader("🚨 APY Movers")

apy_movers = comparison[
    abs(comparison["APY Change"]) > 1
]

st.dataframe(
    apy_movers[
        [
            "Project",
            "Symbol",
            "APY",
            "APY Change",
            "TVL"
        ]
    ],
    use_container_width=True
)

# metrics

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Pools Tracked", len(df))

with col2:
    st.metric(
        "Average APY",
        f"{round(df['APY'].mean(),2)}%"
    )

with col3:
    st.metric(
        "Highest APY",
        f"{round(df['APY'].max(),2)}%"
    )

# charts

st.subheader("Top Scores")

top_df = df.head(10)

st.bar_chart(top_df.set_index("Project")["Score"])