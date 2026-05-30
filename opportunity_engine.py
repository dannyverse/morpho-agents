import pandas as pd

# =========================
# LOAD FUNDING HISTORY
# =========================

df = pd.read_csv(
    "funding_history.csv"
)

# =========================
# CLEAN DATA
# =========================

df["funding_apr"] = pd.to_numeric(
    df["funding_apr"],
    errors="coerce"
)

df = df.dropna()

# =========================
# LOAD ADAPTIVE MEMORY
# =========================

try:

    memory_df = pd.read_csv(
        "signal_memory.csv"
    )

    adaptive_weights = {}

    assets_memory = memory_df["asset"].unique()

    for asset in assets_memory:

        asset_df = memory_df[
            memory_df["asset"] == asset
        ]

        avg_pnl = asset_df["pnl"].mean()

        weight = 1.0

        if avg_pnl > 1:

            weight += 0.5

        elif avg_pnl < 0:

            weight -= 0.3

        adaptive_weights[asset] = round(
            weight,
            2
        )

except:

    adaptive_weights = {}

# =========================
# BUILD OPPORTUNITIES
# =========================

opportunities = []

assets = df["asset"].unique()

for asset in assets:

    asset_df = df[
        df["asset"] == asset
    ]

    avg_funding = round(
        asset_df["funding_apr"].mean(),
        2
    )

    persistence = len(

        asset_df[
            abs(asset_df["funding_apr"]) > 10
        ]
    )

    # =========================
    # BASE SCORE
    # =========================

    score = 0

    if persistence >= 3:

        score += 2

    if abs(avg_funding) > 10:

        score += 2

    if abs(avg_funding) > 20:

        score += 2

    # =========================
    # ADAPTIVE WEIGHT
    # =========================

    adaptive_weight = adaptive_weights.get(
        asset,
        1.0
    )

    final_score = round(
        score * adaptive_weight,
        2
    )

    # =========================
    # SIGNAL GRADE
    # =========================

    if final_score >= 8:

        grade = "A"

    elif final_score >= 5:

        grade = "B"

    else:

        grade = "C"

    # =========================
    # SAVE
    # =========================

    opportunities.append({

        "asset": asset,

        "funding": avg_funding,

        "persistence": persistence,

        "base_score": score,

        "adaptive_weight": adaptive_weight,

        "final_score": final_score,

        "grade": grade
    })

# =========================
# RESULTS
# =========================

op_df = pd.DataFrame(
    opportunities
)

op_df = op_df.sort_values(
    by="final_score",
    ascending=False
)

# =========================
# OUTPUT
# =========================

print("\n🧠 ADAPTIVE OPPORTUNITY ENGINE\n")

for _, row in op_df.head(20).iterrows():

    print(

        f"🟢 {row['grade']} | "

        f"{row['asset']} | "

        f"Base: {row['base_score']} | "

        f"Weight: {row['adaptive_weight']} | "

        f"Final: {row['final_score']} | "

        f"Funding: {row['funding']}% | "

        f"Persistence: {row['persistence']}"
    )