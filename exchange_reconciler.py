"""
Exchange Reconciler

Responsabilidad:

- Comparar el estado de Morpho con Hyperliquid.
- Detectar inconsistencias.
- Clasificar diferencias.
- Delegar acciones de reconciliación a positions.py.

Nunca:

- Abrir operaciones.
- Modificar SQLite directamente.
- Ejecutar SQL de ciclo de vida.

Toda modificación del estado operacional debe realizarse
exclusivamente mediante la API pública de positions.py.
"""

import sqlite3

from positions import close_position

from hyperliquid_client import (
    get_account_state,
    get_order,
)

def reconcile(conn: sqlite3.Connection) -> bool:

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            position_id,
            asset,
            direction,
            entry_price,
            current_price,
            position_size,
            opened_at,
            exchange_order_id,
            stop_loss_order_id,
            take_profit_order_id
        FROM positions
        WHERE status='OPEN'
    """)

    sqlite_positions = cursor.fetchall()

    account_state = get_account_state()
    exchange_positions = account_state.get("assetPositions", [])

    print(f"[RECONCILER] SQLite OPEN positions : {len(sqlite_positions)}")
    print(f"[RECONCILER] Exchange OPEN positions: {len(exchange_positions)}")

    exchange_assets = {
        position["position"]["coin"]
        for position in exchange_positions
    }

    differences = []

    for (
        position_id,
        asset,
        direction,
        entry_price,
        current_price,
        size,
        opened_at,
        exchange_order_id,
        stop_loss_order_id,
        take_profit_order_id,
    ) in sqlite_positions:

        if asset in exchange_assets:
            continue

        difference = {
            "position_id": position_id,
            "asset": asset,
            "direction": direction,
            "size": size,
            "exchange_order_id": exchange_order_id,
            "stop_loss_order_id": stop_loss_order_id,
            "take_profit_order_id": take_profit_order_id,
        }

        # Posición legacy
        if (
            exchange_order_id is None
            and entry_price == 0
        ):
            difference["reconcile_status"] = "LEGACY"

        # Nueva arquitectura
        else:
            try:
                order = get_order(stop_loss_order_id)

                status = order["order"]["status"]

                if status == "filled":
                    difference["reconcile_status"] = "STOP_LOSS"

                else:
                    difference["reconcile_status"] = "UNKNOWN"

            except Exception as e:
                difference["reconcile_status"] = f"ERROR: {e}"

        differences.append(difference)

    print()

    if not differences:
        print("[RECONCILER] No differences detected.")
        return True

    print("[RECONCILER] Missing positions:\n")

    for diff in differences:

        print(
            f"{diff['asset']:10}"
            f"{diff['reconcile_status']:15}"
            f"{diff['direction']:6}"
            f" size={diff['size']}"
        )

    # Execute reconciliation actions

    for diff in differences:

        if diff["reconcile_status"] == "LEGACY":

            close_position(
                conn,
                diff["position_id"],
                0,
            )

            print(
                f"[RECONCILER] Closed LEGACY position {diff['asset']}"
            )

    return False
