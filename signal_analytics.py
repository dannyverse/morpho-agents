import pandas as pd

# =========================
# LOAD MEMORY
# =========================

df = pd.read_csv(
    "signal_memory.csv"
)

# =========================
# BASIC STATS
# =========================

total_signals = len(df)

wins = len(df[df["pnl"] > 0])

losses = len(df[df["pnl"] <= 0])

winrate = round(
    (wins / total_signals) * 100,
    2
)

avg_pnl = round(
    df["pnl"].mean(),
    2
)

# =========================
# OUTPUT
# =========================

print("\n📊 SIGNAL ANALYTICS\n")

print(f"Total Signals: {total_signals}")

print(f"Wins: {wins}")

print(f"Losses: {losses}")

print(f"Winrate: {winrate}%")

print(f"Average PnL: {avg_pnl}%")

# =========================
# BY DIRECTION
# =========================

print("\n⚡ PERFORMANCE BY DIRECTION\n")

direction_stats = (

    df.groupby("direction")["pnl"]

    .agg(["count", "mean"])

)

print(direction_stats)

# =========================
# BY ASSET
# =========================

print("\n🪙 PERFORMANCE BY ASSET\n")

asset_stats = (

    df.groupby("asset")["pnl"]

    .agg(["count", "mean"])

    .sort_values(
        by="mean",
        ascending=False
    )
)

print(asset_stats.head(10))

# =========================
# BEST SIGNALS
# =========================

print("\n🚀 BEST SIGNALS\n")

best = df.sort_values(
    by="pnl",
    ascending=False
)

print(

    best[
        [
            "asset",
            "funding",
            "rsi",
            "trend",
            "direction",
            "pnl"
        ]
    ].head(10)
)

# =========================
# WORST SIGNALS
# =========================

print("\n☠️ WORST SIGNALS\n")

worst = df.sort_values(
    by="pnl",
    ascending=True
)

print(

    worst[
        [
            "asset",
            "funding",
            "rsi",
            "trend",
            "direction",
            "pnl"
        ]
    ].head(10)
)