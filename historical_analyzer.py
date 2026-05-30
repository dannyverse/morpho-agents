import pandas as pd

# =========================
# LOAD CSV
# =========================

df = pd.read_csv("funding_history.csv")

# =========================
# CLEAN DATA
# =========================

df["funding_apr"] = pd.to_numeric(
    df["funding_apr"],
    errors="coerce"
)

df = df.dropna()

# =========================
# GROUP ANALYSIS
# =========================

summary = df.groupby("asset").agg({
    "funding_apr": [
        "mean",
        "max",
        "min",
        "count"
    ]
})

summary.columns = [
    "avg_funding",
    "max_funding",
    "min_funding",
    "snapshots"
]

summary = summary.reset_index()

# =========================
# PERSISTENCE SCORE
# =========================

persistent_scores = []

for asset in df["asset"].unique():

    asset_df = df[df["asset"] == asset]

    persistent = asset_df[
        asset_df["funding_apr"].abs() > 10
    ]

    score = len(persistent)

    persistent_scores.append({
        "asset": asset,
        "persistence_score": score
    })

persistence_df = pd.DataFrame(persistent_scores)

# =========================
# MERGE
# =========================

summary = summary.merge(
    persistence_df,
    on="asset"
)

# =========================
# SORT
# =========================

summary = summary.sort_values(
    by="persistence_score",
    ascending=False
)

# =========================
# OUTPUT
# =========================

print("\n⚡ MOST PERSISTENT FUNDING\n")

for _, row in summary.head(10).iterrows():

    print(
        f"{row['asset']} | "
        f"Avg: {round(row['avg_funding'],2)}% | "
        f"Max: {round(row['max_funding'],2)}% | "
        f"Snapshots >10%: {row['persistence_score']}"
    )