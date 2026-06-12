import requests

TOKEN = "8872667197:AAFsK5fNGqdLhConzEZLkJHgRMLmwWo6aFg"

CHAT_ID = "1615611027"


def send_alert(message):

    url = (
        f"https://api.telegram.org/bot"
        f"{TOKEN}/sendMessage"
    )

    payload = {

        "chat_id": CHAT_ID,

        "text": message
    }

    try:

        response = requests.post(

            url,

            json=payload,

            timeout=5
        )

        return response.json()

    except Exception as e:

        print(
            f"Telegram alert failed: {e}"
        )

        return None


# =========================
# TEST
# =========================

if __name__ == "__main__":

    send_alert(
        "✅ Telegram setup working"
    )

    print(
        "🚀 Telegram test completed"
    )
