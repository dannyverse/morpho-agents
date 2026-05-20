import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Advanced Yield Agent", layout="wide")

st.title("🤖 Advanced DeFi Yield Agent")

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

    # filtros anti basura

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

    # penalizaciones

    if risk == "Medium":
        score -= 15

    if risk == "High":
        score -= 35

    if not trusted:
        score -= 20

    if tvl < 20_000_000:
        score -= 10

    recommendation = "Hold"

    if score < 50:
        recommendation = "Avoid"

    elif score < 70:
        recommendation = "Caution"

    filtered_pools.append({
        "Project": project,
        "Symbol": symbol,
        "Chain": pool.get("chain", ""),
        "APY": round(apy, 2),
        "TVL": round(tvl, 0),
        "Risk": risk,
        "Trusted": trusted,
        "Score": score,
        "Recommendation": recommendation
    })

df = pd.DataFrame(filtered_pools)

df = df.sort_values(by="Score", ascending=False)

st.subheader("Top Stable Opportunities")

st.dataframe(df.head(30), use_container_width=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Safe Opportunities", len(df[df["Risk"] == "Low"]))

with col2:
    st.metric("Medium Risk", len(df[df["Risk"] == "Medium"]))

with col3:
    st.metric("High Risk", len(df[df["Risk"] == "High"]))

st.subheader("Top Scores")

top_df = df.head(10)

st.bar_chart(top_df.set_index("Project")["Score"])