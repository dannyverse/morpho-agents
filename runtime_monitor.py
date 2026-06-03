import json
import os
import tempfile
from datetime import datetime

# =========================
# CONFIG
# =========================

RUNTIME_STATE_FILE = (
    "runtime_state.json"
)

# =========================
# DEFAULT STATE
# =========================

DEFAULT_RUNTIME_STATE = {

    "cycle_id": 0,

    "heartbeat_timestamp": None,

    "system_status": "INITIALIZING",

    "runtime_mode": "NORMAL",

    "active_modules": [],

    "failed_modules": [],

    "last_error": None,

    "heartbeat_ok": True,

    "cycle_duration_seconds": 0,

    "last_successful_cycle": 0
}

# =========================
# WRITE RUNTIME STATE
# =========================

def write_runtime_state(

    cycle_id=0,

    system_status="INITIALIZING",

    runtime_mode="NORMAL",

    active_modules=None,

    failed_modules=None,

    last_error=None,

    heartbeat_ok=True,

    cycle_duration_seconds=0,

    last_successful_cycle=0
):

    if active_modules is None:

        active_modules = []

    if failed_modules is None:

        failed_modules = []

    runtime_state = {

        "cycle_id": cycle_id,

        "heartbeat_timestamp": str(
            datetime.now()
        ),

        "system_status": system_status,

        "runtime_mode": runtime_mode,

        "active_modules": active_modules,

        "failed_modules": failed_modules,

        "last_error": last_error,

        "heartbeat_ok": heartbeat_ok,

        "cycle_duration_seconds": (
            cycle_duration_seconds
        ),

        "last_successful_cycle": (
            last_successful_cycle
        )
    }

    # =========================
    # ATOMIC WRITE
    # =========================

    with tempfile.NamedTemporaryFile(

        "w",

        delete=False

    ) as temp_file:

        json.dump(

            runtime_state,

            temp_file,

            indent=4
        )

        temp_path = temp_file.name

    os.replace(

        temp_path,

        RUNTIME_STATE_FILE
    )

# =========================
# READ RUNTIME STATE
# =========================

def read_runtime_state():

    if not os.path.exists(
        RUNTIME_STATE_FILE
    ):

        write_runtime_state()

    with open(

        RUNTIME_STATE_FILE,

        "r"

    ) as file:

        return json.load(file)

# =========================
# TEST
# =========================

if __name__ == "__main__":

    write_runtime_state(

        cycle_id=1,

        system_status="HEALTHY",

        active_modules=[
            "market_data_agent",
            "risk_manager"
        ],

        failed_modules=[],

        heartbeat_ok=True,

        cycle_duration_seconds=2.4,

        last_successful_cycle=1
    )

    state = read_runtime_state()

    print("\n")
    print("🚀 RUNTIME STATE")
    print("=" * 40)

    print("\n")
    print(json.dumps(
        state,
        indent=4
    ))


