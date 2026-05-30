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