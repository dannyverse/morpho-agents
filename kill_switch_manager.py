import json
import os
import tempfile
from datetime import datetime
from notifier import send_alert

# =========================
# CONFIG
# =========================

KILL_SWITCH_FILE = (
    "kill_switch_state.json"
)

# =========================
# DEFAULT STATE
# =========================

DEFAULT_KILL_SWITCH_STATE = {

    "kill_switch_active": False,

    "activation_timestamp": None,

    "deactivation_timestamp": None,

    "reason": None,

    "activated_by": None,

    "deactivated_by": None,

    "deactivation_reason": None
}

# =========================
# WRITE STATE
# =========================

def write_kill_switch_state(state):

    with tempfile.NamedTemporaryFile(

        "w",

        delete=False

    ) as temp_file:

        json.dump(

            state,

            temp_file,

            indent=4
        )

        temp_path = temp_file.name

    os.replace(

        temp_path,

        KILL_SWITCH_FILE
    )

# =========================
# ACTIVATE
# =========================

def activate_kill_switch(

    reason,

    activated_by="risk_manager"
):

    state = {

        "kill_switch_active": True,

        "activation_timestamp": str(
            datetime.now()
        ),

        "deactivation_timestamp": None,

        "reason": reason,

        "activated_by": activated_by,

        "deactivated_by": None,

        "deactivation_reason": None
    }

    write_kill_switch_state(
        state
    )
    send_alert(

        f"🚨 MORPHO KILL SWITCH ACTIVATED\n\n"

        f"Reason: {reason}\n"

        f"Activated By: {activated_by}"

    )

# =========================
# DEACTIVATE
# =========================

def deactivate_kill_switch(

    deactivation_reason,

    deactivated_by="operator"
):

    current_state = (
        get_kill_switch_state()
    )

    current_state[
        "kill_switch_active"
    ] = False

    current_state[
        "deactivation_timestamp"
    ] = str(
        datetime.now()
    )

    current_state[
        "deactivated_by"
    ] = deactivated_by

    current_state[
        "deactivation_reason"
    ] = deactivation_reason

    write_kill_switch_state(
        current_state
    )

# =========================
# READ STATE
# =========================

def get_kill_switch_state():

    if not os.path.exists(
        KILL_SWITCH_FILE
    ):

        write_kill_switch_state(
            DEFAULT_KILL_SWITCH_STATE
        )

    with open(

        KILL_SWITCH_FILE,

        "r"

    ) as file:

        return json.load(file)

# =========================
# TEST
# =========================

if __name__ == "__main__":

    deactivate_kill_switch(

        deactivation_reason=
        "Manual reset after testing",

        deactivated_by=
        "operator"
    )

    state = (
        get_kill_switch_state()
    )

    print("\n")
    print("✅ KILL SWITCH RESET")
    print("=" * 40)

    print("\n")
    print(json.dumps(
        state,
        indent=4
    ))

