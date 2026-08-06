import requests
import pandas as pd
from notifier import notify

# =========================
# LOAD DEFI DATA
# =========================

url = "https://yields.llama.fi/pools"

response = requests.get(url)

data = response.json()["data"]

df = pd.DataFrame(data)

# =========================
# RISK ANALYSIS
# =========================

alerts = []

for _, row in df.iterrows():

    try:

        project = str(row.get("project", ""))

        chain = str(row.get("chain", ""))

        symbol = str(row.get("symbol", ""))

        apy = float(row.get("apy", 0))

        tvl = float(row.get("tvlUsd", 0))

        stable = bool(row.get("stablecoin", False))

        # =========================
        # RISK SCORE
        # =========================

        risk_score = 0

        # APY risk
        if apy > 100:
            risk_score += 3

        elif apy > 30:
            risk_score += 2

        # TVL risk
        if tvl < 1_000_000:
            risk_score += 3

        elif tvl < 5_000_000:
            risk_score += 2

        # Stablecoin complexity
        if stable:
            risk_score += 1

        # =========================
        # ALERT FILTER
        # =========================

        if risk_score < 4:
            continue

        # =========================
        # RISK LEVEL
        # =========================

        if risk_score >= 7:
            risk_level = "🔴 EXTREME"

        elif risk_score >= 5:
            risk_level = "🟠 HIGH"

        else:
            risk_level = "🟡 MODERATE"

        # =========================
        # BUILD ALERT
        # =========================

        alert = (
            f"{risk_level} RISK YIELD\n\n"
            f"Protocol: {project}\n"
            f"Chain: {chain}\n"
            f"Asset: {symbol}\n"
            f"APY: {round(apy,2)}%\n"
            f"TVL: ${round(tvl/1_000_000,2)}M\n"
            f"Risk Score: {risk_score}/10"
        )

        alerts.append({
            "score": risk_score,
            "message": alert
        })

    except:
        continue

# =========================
# SORT ALERTS
# =========================

alerts = sorted(
    alerts,
    key=lambda x: x["score"],
    reverse=True
)

# =========================
# SEND ALERTS
# =========================

if len(alerts) == 0:

    print("No major risk alerts")

else:

    for alert in alerts[:10]:

        notify(
            level="CRITICAL" if alert["score"] >= 7 else "WARNING",
            title="YIELD RISK ALERT",
            body=alert["message"],
            details={
                "score": alert["score"]
            }
        )

        print(alert["message"])
