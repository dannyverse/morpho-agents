import pandas as pd
import random

# =========================
# LOAD PAPER TRADES
# =========================

df = pd.read_csv("paper_trades.csv")

if df.empty:

    print("No paper trades found")

    exit()

# =========================
# SIMULATE PERFORMANCE
# =========================

results = []

for _, row in df.iterrows():

    asset = row["asset"]

    signal = row["signal"]

    funding = row["funding_apr"]

    # =========================
    # SIMPLE EDGE MODEL
    # =========================

    if signal == "SHORT":

        # higher funding = better short edge
        expected_edge = min(abs(funding) / 10, 5)

    else:

        # negative funding squeeze
        expected_edge = min(abs(funding) / 8, 5)

    # =========================
    # RANDOMIZED SIMULATION
    # =========================

    pnl = round(
        random.uniform(
            -2,
            expected_edge
        ),
        2
    )

    win = pnl > 0

    results.append({
        "asset": asset,
        "signal": signal,
        "funding": funding,
        "pnl_percent": pnl,
        "win": win
    })

# =========================
# RESULTS DATAFRAME
# =========================

results_df = pd.DataFrame(results)

# =========================
# STATS
# =========================

total_trades = len(results_df)

wins = len(
    results_df[
        results_df["win"] == True
    ]
)

losses = total_trades - wins

winrate = round(
    wins / total_trades * 100,
    2
)

avg_pnl = round(
    results_df["pnl_percent"].mean(),
    2
)

# =========================
# OUTPUT
# =========================

print("\n📊 PERFORMANCE TRACKER\n")

print(f"Total Trades: {total_trades}")

print(f"Wins: {wins}")

print(f"Losses: {losses}")

print(f"Winrate: {winrate}%")

print(f"Average PnL: {avg_pnl}%")

print("\n🏆 TRADE RESULTS\n")

for _, row in results_df.iterrows():

    status = (
        "✅ WIN"
        if row["win"]
        else "❌ LOSS"
    )

    print(
        f"{status} | "
        f"{row['asset']} | "
        f"{row['signal']} | "
        f"PnL: {row['pnl_percent']}%"
    )