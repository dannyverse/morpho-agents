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

# =========================
# TEST
# =========================

if __name__ == "__main__":

    send_alert(

        "✅ Telegram .env setup working"
    )

    print(
        "🚀 Telegram test completed"
    )