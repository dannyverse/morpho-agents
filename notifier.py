import os
import requests

from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================

load_dotenv()

TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID"
)

# =========================
# SEND ALERT
# =========================

def send_alert(message):

    try:

        url = (

            f"https://api.telegram.org/bot"

            f"{TOKEN}/sendMessage"
        )

        payload = {

            "chat_id": CHAT_ID,

            "text": message
        }

        response = requests.post(

            url,

            json=payload
        )

        return response.json()

    except Exception as e:

        print(
            f"Telegram Error: {e}"
        )

# =========================
# EXECUTION APPROVED
# =========================

def send_execution_approved(
    asset,
    direction,
    entry_price,
    score,
    confidence,
    signal_strength,
    rationale,
    market_bias,
    decision_health
):

    message = (
        "🟢 EXECUTION APPROVED\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{asset} • {direction}\n\n"
        f"Score: {score}\n"
        f"Confidence: {confidence}%\n"
        f"Signal Strength: {signal_strength}\n\n"
        f"Entry: {entry_price}\n\n"
        f"Reason:\n"
        f"{rationale}\n\n"
        f"AI Bias: {market_bias}\n"
        f"Decision Health: {decision_health}"
    )

    return send_alert(message)        
