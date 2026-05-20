import streamlit as st
import pandas as pd

st.set_page_config(page_title="Morpho Dashboard", layout="wide")

st.title("🚀 Morpho Stable Portfolio Dashboard")

data = {
    "Vault": [
        "Steakhouse Prime USDC",
        "Sentora RLUSD Main",
        "Sentora PYUSD Main",
        "Sky USDS"
    ],
    "Capital": [
        100000,
        60000,
        15000,
        100000
    ],
    "APY": [
        0.032,
        0.055,
        0.050,
        0.045
    ]
}

df = pd.DataFrame(data)

df["Annual Yield"] = df["Capital"] * df["APY"]

total_capital = df["Capital"].sum()
total_yield = df["Annual Yield"].sum()

st.subheader("Portfolio")

st.dataframe(df, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Capital", f"${total_capital:,.0f}")

with col2:
    st.metric("Estimated Annual Yield", f"${total_yield:,.0f}")

st.bar_chart(df.set_index("Vault")["Annual Yield"])
