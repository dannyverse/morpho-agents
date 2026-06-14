import pandas as pd

# =========================
# LOAD MEMORY
# =========================

df = pd.read_csv(
    "signal_memory.csv"
)

# =========================
# BUILD PORTFOLIO
# =========================

portfolio = []

assets = df["asset"].unique()

for asset in assets:

    asset_df = df[
        df["asset"] == asset
    ]

    trades = len(asset_df)

    avg_pnl = round(
        asset_df["pnl"].mean(),
        2
    )

    wins = len(
        asset_df[
            asset_df["pnl"] > 0
        ]
    )

    winrate = round(
        (wins / trades) * 100,
        2
    )

    avg_score = round(
        asset_df["score"].mean(),
        2
    )

    # =========================
    # ALLOCATION SCORE
    # =========================

    allocation_score = 0

    allocation_score += avg_score

    allocation_score += avg_pnl

    allocation_score += (
        winrate / 100
    )

    # =========================
    # CAPITAL WEIGHT
    # =========================

    capital_weight = max(
        0,
        round(allocation_score, 2)
    )
realized_pnl = round(
    asset_df["pnl"].sum(),
    2
)

unrealized_pnl = 0

total_pnl = round(
    realized_pnl + unrealized_pnl,
    2
)
portfolio.append({

        "asset": asset,

        "trades": trades,

        "winrate": winrate,

        "avg_pnl": avg_pnl,

        "realized_pnl": realized_pnl,

        "unrealized_pnl": unrealized_pnl,

        "total_pnl": total_pnl,

        "avg_score": avg_score,

        "allocation_score": round(
            allocation_score,
            2
        ),

        "capital_weight": capital_weight
    })

# =========================
# RESULTS
# =========================

portfolio_df = pd.DataFrame(
    portfolio
)

portfolio_df = portfolio_df.sort_values(
    by="capital_weight",
    ascending=False
)

# =========================
# NORMALIZE %
# =========================

total_weight = portfolio_df[
    "capital_weight"
].sum()

portfolio_df["portfolio_pct"] = round(

    (
        portfolio_df["capital_weight"]
        / total_weight
    ) * 100,

    2
)

# =========================
# OUTPUT
# =========================

print("\n💼 PORTFOLIO MANAGER\n")

print(

    portfolio_df[
        [
            "asset",
            "winrate",
            "avg_pnl",
            "avg_score",
            "portfolio_pct"
        ]
    ].head(15)
)
# ============================
# RECONCILIATION AUDIT
# ============================

print("\n🔍 RECONCILIATION AUDIT\n")

if portfolio_df.empty:

    print("⚠️ WARNING: Portfolio is empty")

if df.empty:

    print("⚠️ WARNING: No executions found")

if not portfolio_df.empty and df.empty:

    print(
        "🚨 INCONSISTENT STATE:"
        " portfolio exists without executions"
    )

if portfolio_df["realized_pnl"].isnull().any():

    print(
        "🚨 INVALID STATE:"
        " realized_pnl contains null values"
    )

if portfolio_df["total_pnl"].isnull().any():

    print(
        "🚨 INVALID STATE:"
        " total_pnl contains null values"
    )

print("✅ Reconciliation audit completed")
