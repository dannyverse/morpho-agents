import requests
import pandas as pd

# =========================
# SETTINGS
# =========================

symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "NEARUSDT"
]

# =========================
# RSI FUNCTION
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
# ANALYSIS
# =========================

results = []

for symbol in symbols:

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

        df = pd.DataFrame(data)

        df.columns = [
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

        df["close"] = pd.to_numeric(
            df["close"]
        )

        # =========================
        # INDICATORS
        # =========================

        df["ema_50"] = (
            df["close"]
            .ewm(span=50)
            .mean()
        )

        df["ema_200"] = (
            df["close"]
            .ewm(span=200)
            .mean()
        )

        df["rsi"] = calculate_rsi(
            df["close"]
        )

        latest = df.iloc[-1]

        price = latest["close"]

        ema_50 = latest["ema_50"]

        ema_200 = latest["ema_200"]

        rsi = latest["rsi"]

        # =========================
        # TREND
        # =========================

        if ema_50 > ema_200:

            trend = "BULLISH"

        else:

            trend = "BEARISH"

        # =========================
        # RSI STATE
        # =========================

        if rsi > 70:

            regime = "OVERBOUGHT"

        elif rsi < 30:

            regime = "OVERSOLD"

        else:

            regime = "NEUTRAL"

        results.append({
            "symbol": symbol,
            "price": round(price, 2),
            "trend": trend,
            "rsi": round(rsi, 2),
            "regime": regime
        })

    except Exception as e:

        print(f"Error on {symbol}: {e}")

# =========================
# OUTPUT
# =========================

results_df = pd.DataFrame(results)

print("\n📈 TECHNICAL AGENT\n")

for _, row in results_df.iterrows():

    print(
        f"{row['symbol']} | "
        f"{row['trend']} | "
        f"RSI: {row['rsi']} | "
        f"{row['regime']} | "
        f"Price: ${row['price']}"
    )