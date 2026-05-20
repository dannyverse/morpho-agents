import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Live Morpho Dashboard", layout="wide")

st.title("🚀 Live DeFi Yield Dashboard")

url = "https://api.llama.fi/protocols"

response = requests.get(url)

protocols = response.json()

morpho_data = []

for protocol in protocols:
    name = protocol.get("name", "")
    
    if "morpho" in name.lower():
        morpho_data.append({
            "Protocol": name,
            "TVL": protocol.get("tvl", 0),
            "Chain": protocol.get("chain", ""),
            "Category": protocol.get("category", "")
        })

df = pd.DataFrame(morpho_data)

st.subheader("Morpho Ecosystem")

st.dataframe(df, use_container_width=True)

st.metric("Protocols Found", len(df))
