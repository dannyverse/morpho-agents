import os
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DB = "trading_system.db"


def send_message(text):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text,
        },
        timeout=10,
    )


def get_updates(offset=None):

    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    params = {}

    if offset:
        params["offset"] = offset

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    return response.json()


def get_positions():

    conn = sqlite3.connect(DB)

    rows = conn.execute(
        """
        SELECT
            asset,
            direction,
            position_size,
            unrealized_pnl
        FROM portfolio_state
        WHERE status='OPEN'
        """
    ).fetchall()

    conn.close()

    return rows


def get_health():

    conn = sqlite3.connect(DB)

    rows = conn.execute(
        """
        SELECT
            module,
            status
        FROM system_health
        ORDER BY timestamp DESC
        LIMIT 5
        """
    ).fetchall()

    conn.close()

    return rows

def get_risk():

    conn = sqlite3.connect(DB)

    row = conn.execute(
        """
        SELECT
            market_regime,
            equity,
            exposure,
            open_positions,
            health_score,
            system_status
        FROM system_log
        ORDER BY ROWID DESC
        LIMIT 1
        """
    ).fetchone()

    conn.close()

    return row

def get_status():

    positions = get_positions()
    health = get_health()

    message = []

    message.append(
        "🧠 MORPHO STATUS"
    )

    message.append(
        "━━━━━━━━━━━━━━━━"
    )

    message.append(
        "\n🟢 SYSTEM"
    )

    for module, status in health:
        message.append(
            f"{module}: {status}"
        )

    message.append(
        "\n📊 OPEN POSITIONS"
    )

    if positions:

        for asset, direction, size, pnl in positions:

            message.append(
                f"""
{asset} {direction}
Size: {size}
PnL: {pnl}
"""
            )

    else:

        message.append(
            "No open positions"
        )


    message.append(
        "\n🔐 AUTHORITY"
    )

    message.append(
        "Live Execution: BLOCKED"
    )

    return "\n".join(message)

def handle_command(command):

    if command == "/status":

        send_message(
            get_status()
        )

    elif command == "/opportunities":

        import csv

        message = "⚡ FUNDING OPPORTUNITIES\n\n"

        try:
            with open("funding_history.csv", "r") as file:

                rows = list(csv.DictReader(file))

            for row in rows[-5:]:

                message += (
                    f"🪙 {row['asset']}\n"
                    f"📈 APR: {round(float(row['funding_apr']),2)}%\n"
                    f"💰 OI: ${round(float(row['open_interest'])/1_000_000,2)}M\n"
                    f"🔄 Volume: ${round(float(row['volume'])/1_000_000,2)}M\n\n"
                )

        except Exception as e:

            message = f"Error reading opportunities: {e}"

        send_message(message)

    elif command == "/positions":

        positions = get_positions()

        message = "📊 OPEN POSITIONS\n\n"

        if not positions:

            message += "No open positions"

        else:

            for position in positions:

                asset, direction, size, pnl = position

                message += (
                    f"🪙 {asset}\n"
                    f"📌 {direction}\n"
                    f"📦 Size: {size}\n"
                    f"💰 PnL: {pnl}\n\n"
                )

        send_message(message)

    elif command == "/risk":

        risk = get_risk()

        message = "🛡️ MORPHO RISK\n\n"

        if not risk:

            message += "No risk data available"

        else:

            market, equity, exposure, positions, health, status = risk

            message += (
                f"🌐 Market: {market}\n"
                f"💰 Equity: ${equity}\n"
                f"📊 Exposure: {exposure}%\n"
                f"📂 Open Positions: {positions}\n"
                f"❤️ Health Score: {health}\n"
                f"⚙️ System: {status}\n"
            )

        send_message(message)

def run():

    print(
        "Telegram interface started"
    )

    offset = None

    while True:

        updates = get_updates(offset)

        for update in updates.get("result", []):

            offset = update["update_id"] + 1

            message = update.get(
                "message",
                {}
            )

            if not message:
                continue

            chat_id = str(
                message["chat"]["id"]
            )

            if chat_id != str(CHAT_ID):
                continue

            text = message.get(
                "text",
                ""
            )

            handle_command(text)


if __name__ == "__main__":
    run()
