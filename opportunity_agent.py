import pandas as pd
import requests

# =========================
# LOAD FUNDING DATA
# =========================

df = pd.read_csv("funding_history.csv")

# =========================
# CLEAN
# =========================

df["funding_apr"] = pd.to_numeric(
    df["funding_apr"],
    errors="coerce"
)

df = df.dropna()

# =========================
# TECHNICAL FUNCTION
# =========================

def calculate_rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# =========================
# ANALYZE ASSETS
# =========================

results = []

for asset in df["asset"].unique():

    asset_df = df[
        df["asset"] == asset
    ]

    avg_funding = round(
        asset_df["funding_apr"].mean(),
        2
    )

    max_funding = round(
        asset_df["funding_apr"].max(),
        2
    )

    persistence = len(
        asset_df[
            abs(asset_df["funding_apr"]) > 10
        ]
    )

    # =========================
    # BINANCE SYMBOL
    # =========================

    symbol = f"{asset}USDT"

    try:

        url = (
            "https://api.binance.com/api/v3/klines"
        )

        params = {
            "symbol": symbol,
            "interval": "1h",
            "limit": 200
        }

        response = requests.get(
            url,
            params=params
        )

        data = response.json()

        tech_df = pd.DataFrame(data)

        tech_df.columns = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore"
        ]

        tech_df["close"] = pd.to_numeric(
            tech_df["close"]
        )

        # =========================
        # INDICATORS
        # =========================

        tech_df["ema_50"] = (
            tech_df["close"]
            .ewm(span=50)
            .mean()
        )

        tech_df["ema_200"] = (
            tech_df["close"]
            .ewm(span=200)
            .mean()
        )

        tech_df["rsi"] = calculate_rsi(
            tech_df["close"]
        )

        latest = tech_df.iloc[-1]

        rsi = round(latest["rsi"], 2)

        ema_50 = latest["ema_50"]

        ema_200 = latest["ema_200"]

        if ema_50 > ema_200:

            trend = "BULLISH"

        else:

            trend = "BEARISH"

        # =========================
        # CONVICTION SCORE
        # =========================

        score = 0

        # funding persistence
        if persistence >= 3:

            score += 2

        # extreme funding
        if abs(avg_funding) > 20:

            score += 2

        # RSI extremes
        if rsi > 75 or rsi < 25:

            score += 2

        # trend alignment
        if (
            avg_funding > 0
            and trend == "BULLISH"
        ):

            score += 1

        if (
            avg_funding < 0
            and trend == "BEARISH"
        ):

            score += 1

        results.append({
            "asset": asset,
            "avg_funding": avg_funding,
            "max_funding": max_funding,
            "persistence": persistence,
            "trend": trend,
            "rsi": rsi,
            "score": score
        })

    except Exception:

        continue

# =========================
# RESULTS
# =========================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="score",
    ascending=False
)

# =========================
# OUTPUT
# =========================

print("\n🧠 MULTI-FACTOR OPPORTUNITY ENGINE\n")

for _, row in results_df.iterrows():

    print(
        f"{row['asset']} | "
        f"Score: {row['score']} | "
        f"Funding: {row['avg_funding']}% | "
        f"RSI: {row['rsi']} | "
        f"{row['trend']} | "
        f"Persistence: {row['persistence']}"
    )