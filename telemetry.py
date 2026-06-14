from datetime import datetime
import json


def log_market_event(
    event,
    status,
    details=None
):

    log_entry = {
        "timestamp": str(datetime.utcnow()),
        "event": event,
        "status": status,
        "details": details or {}
    }

    with open(
        "market_events.log",
        "a"
    ) as log_file:

        log_file.write(
            json.dumps(log_entry)
            + "\n"
        )
