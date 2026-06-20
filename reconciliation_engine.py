import sqlite3
import pandas as pd


print(
    "\n🔍 RECONCILIATION ENGINE\n"
)

conn = sqlite3.connect(
    "trading_system.db"
)

portfolio_df = pd.read_sql(
    """
    SELECT *
    FROM portfolio_state
    """,
    conn
)

conn.close()

issues_found = 0


# ============================
# EMPTY CHECK
# ============================

if portfolio_df.empty:

    print(
        "ℹ️ No open positions found."
    )

else:

    # ============================
    # SCHEMA CHECK
    # ============================

    required_columns = [

        "asset",

        "direction",

        "entry_price",

        "position_size",

        "status"
    ]

    for column in required_columns:

        if column not in portfolio_df.columns:

            print(
                f"❌ Missing column: {column}"
            )

            issues_found += 1

    # ============================
    # POSITION CHECK
    # ============================

    for _, row in portfolio_df.iterrows():

        asset = row["asset"]

        if pd.isna(
            row["direction"]
        ):

            print(
                f"❌ Missing direction: {asset}"
            )

            issues_found += 1

        if pd.isna(
            row["entry_price"]
        ):

            print(
                f"❌ Missing entry price: {asset}"
            )

            issues_found += 1

        if pd.isna(
            row["position_size"]
        ):

            print(
                f"❌ Missing position size: {asset}"
            )

            issues_found += 1

        if row["status"] != "OPEN":

            print(
                f"⚠️ Non-open position: {asset}"
            )

# ============================
# RESULT
# ============================

if issues_found == 0:

    print(
        "\n✅ Reconciliation successful."
    )

else:

    print(
        f"\n⚠️ Issues detected: {issues_found}"
    )
