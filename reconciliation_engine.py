import json
import sqlite3
import pandas as pd


# ============================
# LOAD POSITION STATE
# ============================

with open(
    "state/position_state.json",
    "r"
) as f:

    position_state = json.load(f)


# ============================
# LOAD EXECUTIONS
# ============================

conn = sqlite3.connect(
    "trading_system.db"
)

executions_df = pd.read_sql(
    """
    SELECT *
    FROM executions
    """,
    conn
)

conn.close()


# ============================
# APPROVED EXECUTIONS ONLY
# ============================

approved_df = executions_df[
    executions_df[
        "execution_decision"
    ] == "APPROVED"
]


# ============================
# RECONCILIATION AUDIT
# ============================

print(
    "\n🔍 RECONCILIATION ENGINE\n"
)

issues_found = 0


# ============================
# CHECK 1
# EXECUTION -> POSITION
# ============================

for _, execution in approved_df.iterrows():

    asset = execution["asset"]

    if asset not in position_state:

        print(
            f"❌ Missing position_state entry: {asset}"
        )

        issues_found += 1

        continue

    position = position_state[asset]

    if (
        position["side"]
        !=
        execution["direction"]
    ):

        print(
            f"❌ Direction mismatch: {asset}"
        )

        issues_found += 1

    if (
        position["entry_price"]
        !=
        execution["entry_price"]
    ):

        print(
            f"❌ Entry price mismatch: {asset}"
        )

        issues_found += 1


# ============================
# CHECK 2
# POSITION -> EXECUTION
# ============================

approved_assets = set(
    approved_df["asset"]
)

for asset in position_state:

    if asset not in approved_assets:

        print(
            f"❌ Orphaned position: {asset}"
        )

        issues_found += 1


# ============================
# FINAL RESULT
# ============================

if issues_found == 0:

    print(
        "✅ Reconciliation healthy"
    )

else:

    print(
        f"\n⚠️ Issues detected: {issues_found}"
    )
