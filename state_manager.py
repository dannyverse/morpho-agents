import json
import os

# =========================
# STATE FILES
# =========================

RUNTIME_STATE_FILE = (
    "runtime_state.json"
)

# =========================
# STATE MANAGER
# =========================

class StateManager:

    # =========================
    # RUNTIME STATE
    # =========================

    @staticmethod
    def get_runtime_state():

        if not os.path.exists(
            RUNTIME_STATE_FILE
        ):

            return None

        with open(

            RUNTIME_STATE_FILE,

            "r"

        ) as file:

            return json.load(file)

# =========================
# TEST
# =========================

if __name__ == "__main__":

    runtime_state = (
        StateManager.get_runtime_state()
    )

    print("\n")
    print("🩺 RUNTIME STATE")
    print("=" * 40)

    print("\n")
    print(runtime_state)
