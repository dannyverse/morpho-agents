import hashlib
import json
from pathlib import Path
from typing import Any

STATE_FILE = Path("notification_state.json")


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2,
            sort_keys=True,
        )
    )


def _fingerprint(
    payload: dict[str, Any] | None = None,
) -> str:
    payload = payload or {}

    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()


def is_duplicate(
    event_key: str,
    payload: dict[str, Any] | None = None,
) -> bool:
    state = _load_state()
    return state.get(event_key) == _fingerprint(payload)


def commit_delivery(
    event_key: str,
    payload: dict[str, Any] | None = None,
) -> None:
    state = _load_state()
    state[event_key] = _fingerprint(payload)
    _save_state(state)


def clear(event_key: str) -> None:
    state = _load_state()

    if event_key in state:
        del state[event_key]
        _save_state(state)
