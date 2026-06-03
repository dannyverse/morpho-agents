import json
import os
import tempfile
from datetime import datetime

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

    "reason": None,

    "activated_by": None
}

# =========================
# WRITE STATE
# =========================

def write_kill_switch_state(

    kill_switch_active=False,

    reason=None,

    activated_by=None
):

    state = {

        "kill_switch_active": (
            kill_switch_active
        ),

        "activation_timestamp": str(
            datetime.now()
        ),

        "reason": reason,

        "activated_by": activated_by
    }

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

    write_kill_switch_state(

        kill_switch_active=True,

        reason=reason,

        activated_by=activated_by
    )

# =========================
# READ STATE
# =========================

def get_kill_switch_state():

    if not os.path.exists(
        KILL_SWITCH_FILE
    ):

        write_kill_switch_state()

    with open(

        KILL_SWITCH_FILE,

        "r"

    ) as file:

        return json.load(file)

# =========================
# TEST
# =========================

if __name__ == "__main__":

    activate_kill_switch(

        reason="TEST_EXPOSURE_LIMIT"
    )

    state = (
        get_kill_switch_state()
    )

    print("\n")
    print("🚨 KILL SWITCH STATE")
    print("=" * 40)

    print("\n")
    print(json.dumps(
        state,
        indent=4
    ))
