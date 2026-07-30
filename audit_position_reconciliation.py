from hyperliquid_client import get_account_state
import sqlite3

state = get_account_state()

conn = sqlite3.connect("trading_system.db")
conn.row_factory = sqlite3.Row

sqlite_open = {
    row["asset"]: row
    for row in conn.execute("""
        SELECT *
        FROM positions
        WHERE status='OPEN'
    """)
}

print("\n==============================")
print("POSITIONS MISSING IN SQLITE")
print("==============================")

for asset in state.get("assetPositions", []):
    pos = asset["position"]

    size = float(pos["szi"])
    if size == 0:
        continue

    coin = pos["coin"]

    if coin in sqlite_open:
        continue

    print(f"\n{coin}")
    print(f"  Size       : {size}")
    print(f"  Entry      : {pos.get('entryPx')}")
    print(f"  Unrealized : {pos.get('unrealizedPnl')}")

    rows = conn.execute("""
        SELECT
            position_id,
            status,
            exchange_order_id,
            opened_at,
            updated_at
        FROM positions
        WHERE asset=?
        ORDER BY opened_at DESC
    """, (coin,)).fetchall()

    if not rows:
        print("  SQLite     : NO RECORD FOUND")
    else:
        print("  SQLite history:")
        for r in rows:
            print(
                f"    {r['status']:6} "
                f"OID={r['exchange_order_id']} "
                f"opened={r['opened_at']} "
                f"updated={r['updated_at']}"
            )
