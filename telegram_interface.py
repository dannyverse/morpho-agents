import logging
import os
import time

import requests
from dotenv import load_dotenv

from ops_command_router import CommandRequest, OpsCommandRouter


logger = logging.getLogger(__name__)


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_message(text, chat_id=None):
    destination = str(chat_id if chat_id is not None else CHAT_ID)
    if not TOKEN or not CHAT_ID or destination != str(CHAT_ID):
        return False

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": destination,
                "text": text,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        return isinstance(payload, dict) and payload.get("ok") is True
    except (requests.RequestException, ValueError, TypeError) as exc:
        logger.warning(
            "telegram_send_failed error=%s",
            type(exc).__name__,
        )
        return False


def get_updates(offset=None):
    if not TOKEN or not CHAT_ID:
        return None

    params = {}
    if offset is not None:
        params["offset"] = offset

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError, TypeError) as exc:
        logger.warning(
            "telegram_poll_failed error=%s",
            type(exc).__name__,
        )
        return None

    if not isinstance(payload, dict) or not isinstance(payload.get("result"), list):
        logger.warning("telegram_poll_invalid_payload")
        return None
    return payload


def process_update(update, router, sender=send_message):
    if not isinstance(update, dict):
        return
    message = update.get("message")
    if not isinstance(message, dict):
        return
    chat = message.get("chat")
    if not isinstance(chat, dict) or "id" not in chat:
        return

    chat_id = str(chat["id"])
    if chat_id != str(CHAT_ID):
        return

    text = message.get("text")
    if not isinstance(text, str):
        return
    sender_info = message.get("from")
    user_id = (
        str(sender_info.get("id"))
        if isinstance(sender_info, dict) and sender_info.get("id") is not None
        else None
    )
    response = router.route(
        CommandRequest(
            text=text,
            chat_id=chat_id,
            user_id=user_id,
            update_id=update.get("update_id"),
        )
    )
    sender(response, chat_id)


def process_updates(updates, offset, router, sender=send_message):
    """Process each Telegram update at most once within this process.

    A valid update_id advances the in-memory offset before dispatch. V2 is
    read-only, so malformed, unauthorized, or failed-response updates are not
    replayed indefinitely.
    """
    for update in updates:
        if isinstance(update, dict) and isinstance(update.get("update_id"), int):
            candidate_offset = update["update_id"] + 1
            offset = max(offset or candidate_offset, candidate_offset)
        try:
            process_update(update, router, sender)
        except Exception as exc:
            logger.warning(
                "telegram_update_processing_failed error=%s",
                type(exc).__name__,
            )
    return offset


def run():
    print("Telegram interface started")
    offset = None
    router = OpsCommandRouter()

    while True:
        payload = get_updates(offset)
        if payload is None:
            time.sleep(1)
            continue

        offset = process_updates(payload["result"], offset, router)


if __name__ == "__main__":
    run()
