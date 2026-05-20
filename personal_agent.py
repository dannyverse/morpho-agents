import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Personal Treasury Agent", layout="wide")

st.title("🧠 Personal Treasury Agent")

url = "https://yields.llama.fi/pools"

response = requests.get(url)

data = response.json()["data"]

# =========================
# WATCHLIST
# =========================

watchlist_keywords = [
    "RLUSD",
    "PYUSD",
    "USDS",
    "USDC"
]

favorite_protocols = [
    "morpho-blue",
    "aave-v3",
    "sky",
    "spark",
    "compound-v3"
]

tracked_pools = []

for pool in data:

    symbol = str(pool.get("symbol", "")).upper()
    project = str(pool.get("project", "")).lower()

    if not any(keyword in symbol for keyword in watchlist_keywords):
        continue

    if project not in favorite_protocols:
        continue

    apy = pool.get("apy", 0)
    tvl = pool.get("tvlUsd", 0)

    if apy is None or tvl is None:
        continue

    if tvl < 5_000_000:
        continue

    risk = "Low"

    if apy > 8:
        risk = "High"

    elif apy > 5:
        risk = "Medium"

    score = 100

    if risk == "Medium":
        score -= 15

    if risk == "High":
        score -= 35

    if tvl < 20_000_000:
        score -= 10

    tracked_pools.append({
        "Project": project,
        "Symbol": symbol,
        "Chain": pool.get("chain", ""),
        "APY": round(apy, 2),
        "TVL": round(tvl, 0),
        "Risk": risk,
        "Score": score
    })

df = pd.DataFrame(tracked_pools)

df = df.sort_values(by="Score", ascending=False)

# =========================
# HISTORY
# =========================

history_file = "personal_history.csv"

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

df.to_csv(history_file, index=False)

# =========================
# ALERT ENGINE
# =========================

alerts = []

for _, row in comparison.iterrows():

    if row["APY Change"] > 1:
        alerts.append(
            f"🟢 {row['Symbol']} APY increased by {round(row['APY Change'],2)}%"
        )

    if row["APY Change"] < -1:
        alerts.append(
            f"🔴 {row['Symbol']} APY dropped by {round(abs(row['APY Change']),2)}%"
        )

    if row["TVL Change"] < -10_000_000:
        alerts.append(
            f"⚠️ {row['Symbol']} lost significant liquidity"
        )

# =========================
# DASHBOARD
# =========================

st.subheader("📊 Your Stable Watchlist")

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
    ],
    use_container_width=True
)

# =========================
# AI PICKS
# =========================

st.subheader("🤖 AI Top Picks")

top_picks = comparison[
    (comparison["Risk"] == "Low") &
    (comparison["APY"] > 3)
]

top_picks = top_picks.sort_values(
    by=["APY", "TVL"],
    ascending=[False, False]
)

for _, row in top_picks.head(5).iterrows():

    st.success(
        f"""
        ✅ {row['Symbol']} on {row['Project']}

        APY: {row['APY']}%

        TVL: ${row['TVL']:,.0f}

        Chain: {row['Chain']}

        Score: {row['Score']}
        """
    )

# =========================
# ALERTS
# =========================

st.subheader("🚨 Alerts")

if len(alerts) == 0:

    st.success("No important changes detected")

else:

    for alert in alerts:
        st.warning(alert)

# =========================
# METRICS
# =========================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Tracked Vaults", len(df))

with col2:
    st.metric(
        "Average APY",
        f"{round(df['APY'].mean(),2)}%"
    )

with col3:
    safest = df[df["Risk"] == "Low"]

    st.metric(
        "Low Risk Vaults",
        len(safest)
    )

# =========================
# CHART
# =========================

st.subheader("🏆 Best Opportunities")

top_df = df.head(10)

st.bar_chart(top_df.set_index("Symbol")["APY"])