import os
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv
from notification_state import should_send

# =========================
# LOAD ENV
# =========================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# =========================
# OPERATIONS CENTER LEVELS
# =========================

LEVEL_ICONS = {
    "INFO": "🔵",
    "SUCCESS": "🟢",
    "WARNING": "🟠",
    "ERROR": "🔴",
    "CRITICAL": "🚨",
}


# =========================
# TELEGRAM TRANSPORT
# =========================

def send_alert(message: str) -> dict[str, Any] | None:
    """
    Backwards-compatible Telegram sender.

    Existing Morpho modules may continue calling send_alert(message)
    while new operational events use notify().
    """

    if not TOKEN or not CHAT_ID:
        print("Telegram Error: missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return None

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": message,
        }

        response = requests.post(
            url,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:
        print(f"Telegram Error: {exc}")
        return None


# =========================
# MESSAGE BUILDER
# =========================

def build_message(
    level: str,
    title: str,
    body: str | None = None,
    details: dict[str, Any] | None = None,
) -> str:
    normalized_level = level.upper()

    if normalized_level not in LEVEL_ICONS:
        raise ValueError(
            f"Unsupported notification level: {level}"
        )

    icon = LEVEL_ICONS[normalized_level]

    lines = [
        f"{icon} {normalized_level} · {title.upper()}",
        "━━━━━━━━━━━━━━━━━━",
    ]

    if body:
        lines.extend([
            "",
            str(body),
        ])

    if details:
        lines.append("")

        for key, value in details.items():
            lines.append(f"{key}: {value}")

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    lines.extend([
        "",
        f"Time: {timestamp}",
    ])

    return "\n".join(lines)


# =========================
# OPERATIONS CENTER API
# =========================

def notify(
    level: str,
    title: str,
    body: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Send a uniformly formatted Morpho operational notification.
    """

    payload = {
        "level": level,
        "title": title,
        "body": body,
        "details": details or {},
    }

    always_send = {
        "SYSTEM STARTUP",
        "EXECUTION APPROVED",
    }

    if title.upper() not in always_send:
        decision = should_send(title.upper(), payload)

        if not decision:
            return None

    message = build_message(
        level=level,
        title=title,
        body=body,
        details=details,
    )

    return send_alert(message)

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
    decision_health,
):
    return notify(
        level="SUCCESS",
        title="Execution Approved",
        body=f"{asset} · {direction}",
        details={
            "Entry": entry_price,
            "Score": score,
            "Confidence": f"{confidence}%",
            "Signal Strength": signal_strength,
            "Reason": rationale,
            "AI Bias": market_bias,
            "Decision Health": decision_health,
        },
    )
