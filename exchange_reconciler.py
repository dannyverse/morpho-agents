"""
Exchange Reconciler

Responsabilidad:

- Comparar las posiciones OPEN de SQLite con las posiciones reales
  existentes en Hyperliquid.
- Detectar posiciones que ya no existen en el exchange.
- Confirmar su cierre mediante fills reales de Hyperliquid.
- Obtener el PnL realizado directamente del exchange.
- Delegar el cambio de estado local a positions.close_position().

Este módulo no abre posiciones ni ejecuta órdenes.
"""

import sqlite3

from hyperliquid_client import get_account_state, get_info
from hyperliquid_poc.config import ACCOUNT_ADDRESS
from positions import close_position


def _normalize_order_id(order_id):
    """
    Convierte un identificador de orden a entero.

    Devuelve None cuando el identificador está ausente
    o no puede convertirse.
    """
    if order_id is None:
        return None

    try:
        return int(order_id)
    except (TypeError, ValueError):
        return None


def _is_close_fill(fill, asset):
    """
    Determina si un fill corresponde al cierre de una posición
    del activo indicado.
    """
    if fill.get("coin") != asset:
        return False

    direction = str(fill.get("dir", ""))

    return direction.startswith("Close ")


def _find_close_fill(
    fills,
    asset,
    stop_loss_order_id,
    take_profit_order_id,
):
    """
    Busca el fill de cierre más reciente de un activo.

    Prioridad de clasificación:

    1. STOP_LOSS:
       El OID del fill coincide con stop_loss_order_id.

    2. TAKE_PROFIT:
       El OID del fill coincide con take_profit_order_id.

    3. EXCHANGE_CLOSE:
       Existe un fill real de cierre, pero no coincide con las
       órdenes protectoras conocidas. Puede ser un cierre manual,
       externo o una orden cuyo ID no fue persistido correctamente.

    Devuelve:

        (fill, motivo)

    o:

        (None, "UNKNOWN")
    """
    normalized_stop_loss_id = _normalize_order_id(
        stop_loss_order_id
    )
    normalized_take_profit_id = _normalize_order_id(
        take_profit_order_id
    )

    close_fills = [
        fill
        for fill in fills
        if _is_close_fill(fill, asset)
    ]

    if not close_fills:
        return None, "UNKNOWN"

    close_fills.sort(
        key=lambda fill: int(fill.get("time", 0)),
        reverse=True,
    )

    for fill in close_fills:
        fill_order_id = _normalize_order_id(
            fill.get("oid")
        )

        if (
            normalized_stop_loss_id is not None
            and fill_order_id == normalized_stop_loss_id
        ):
            return fill, "STOP_LOSS"

        if (
            normalized_take_profit_id is not None
            and fill_order_id == normalized_take_profit_id
        ):
            return fill, "TAKE_PROFIT"

    return close_fills[0], "EXCHANGE_CLOSE"


def reconcile(conn: sqlite3.Connection) -> bool:
    """
    Reconcilia las posiciones locales con Hyperliquid.

    Una posición local solamente se cierra cuando:

    - ya no aparece abierta en Hyperliquid; y
    - existe evidencia suficiente de su cierre.

    Las posiciones modernas sin fill verificable permanecen OPEN
    para evitar cierres locales falsos.

    Devuelve True cuando no quedan diferencias sin resolver.
    Devuelve False cuando existe alguna posición no resuelta.
    """
    cursor = conn.cursor()

    cursor.execute(
        """
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
        WHERE status = 'OPEN'
        """
    )

    sqlite_positions = cursor.fetchall()

    account_state = get_account_state()

    exchange_positions = account_state.get(
        "assetPositions",
        [],
    )

    exchange_assets = {
        position_data["position"]["coin"]
        for position_data in exchange_positions
        if position_data.get("position")
        and position_data["position"].get("coin")
    }

    info = get_info()
    fills = info.user_fills(ACCOUNT_ADDRESS)

    print(
        "[RECONCILER] SQLite OPEN positions: "
        f"{len(sqlite_positions)}"
    )

    print(
        "[RECONCILER] Exchange OPEN positions: "
        f"{len(exchange_positions)}"
    )

    differences = []

    for row in sqlite_positions:
        (
            position_id,
            asset,
            direction,
            entry_price,
            current_price,
            position_size,
            opened_at,
            exchange_order_id,
            stop_loss_order_id,
            take_profit_order_id,
        ) = row

        if asset in exchange_assets:
            continue

        difference = {
            "position_id": position_id,
            "asset": asset,
            "direction": direction,
            "position_size": position_size,
            "opened_at": opened_at,
            "realized_pnl": None,
            "reconcile_status": "UNKNOWN",
        }

        is_legacy_position = (
            exchange_order_id is None
            and float(entry_price or 0) == 0
        )

        if is_legacy_position:
            difference["reconcile_status"] = "LEGACY"
            difference["realized_pnl"] = 0.0

            differences.append(difference)
            continue

        close_fill, close_reason = _find_close_fill(
            fills=fills,
            asset=asset,
            stop_loss_order_id=stop_loss_order_id,
            take_profit_order_id=take_profit_order_id,
        )

        difference["reconcile_status"] = close_reason

        if close_fill is not None:
            try:
                difference["realized_pnl"] = float(
                    close_fill.get("closedPnl", 0)
                )
            except (TypeError, ValueError):
                difference["realized_pnl"] = None
                difference["reconcile_status"] = (
                    "INVALID_CLOSED_PNL"
                )

            difference["close_price"] = close_fill.get("px")
            difference["close_order_id"] = close_fill.get("oid")
            difference["close_time"] = close_fill.get("time")

        differences.append(difference)

    print()

    if not differences:
        print(
            "[RECONCILER] No differences detected."
        )
        return True

    print("[RECONCILER] Missing exchange positions:")
    print()

    unresolved = False

    for difference in differences:
        print(
            f"{difference['asset']:10} "
            f"{difference['reconcile_status']:20} "
            f"{difference['direction']:8} "
            f"size={difference['position_size']} "
            f"pnl={difference['realized_pnl']}"
        )

        if difference["realized_pnl"] is None:
            unresolved = True

            print(
                "[RECONCILER] Position remains OPEN: "
                f"{difference['asset']} has no verified "
                "exchange close fill."
            )

            continue

        close_position(
            conn,
            difference["position_id"],
            difference["realized_pnl"],
        )

        print(
            f"[RECONCILER] Closed {difference['asset']} "
            f"reason={difference['reconcile_status']} "
            f"realized_pnl="
            f"{difference['realized_pnl']}"
        )

    conn.commit()

    return not unresolved
