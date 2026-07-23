"""
Execution Workflow

Responsabilidad:

- Orquestar la ejecución contra Hyperliquid.
- NO escribir en SQLite.
- NO enviar notificaciones.
- NO conocer execution_agent.

Devuelve únicamente un ExecutionResult.
"""

from dataclasses import dataclass
import pprint
import time

from hyperliquid_client import get_exchange, get_info
from positions import (
    calculate_stop_loss,
    calculate_take_profit,
)


exchange = get_exchange()


@dataclass
class ExecutionResult:
    success: bool
    position_open: bool = False
    exchange_order_id: str | None = None
    stop_loss_order_id: str | None = None
    take_profit_order_id: str | None = None
    entry_price: float | None = None
    error: str | None = None


def _get_first_status(response) -> dict | None:
    """
    Extrae el primer status de una respuesta de Hyperliquid.
    """

    if not isinstance(response, dict):
        return None

    try:
        statuses = (
            response
            .get("response", {})
            .get("data", {})
            .get("statuses", [])
        )
    except AttributeError:
        return None

    if not statuses:
        return None

    status = statuses[0]

    if not isinstance(status, dict):
        return None

    return status


def _extract_resting_order_id(response) -> str | None:
    """
    Extrae el OID de una orden resting confirmada.
    """

    print("\n" + "=" * 80)
    print("FULL ORDER RESPONSE")
    pprint.pp(response, sort_dicts=False)
    print("=" * 80)

    status = _get_first_status(response)

    if status is None:
        print("No statuses found")
        return None

    print("STATUS:", status)
    print("STATUS KEYS:", list(status.keys()))

    resting = status.get("resting")

    if (
        isinstance(resting, dict)
        and resting.get("oid") is not None
    ):
        print("RESTING:", resting)
        return str(resting["oid"])

    if "filled" in status:
        print("FILLED:", status["filled"])

    if "error" in status:
        print("ERROR:", status["error"])

    print("No resting order id found.")

    return None


def _extract_filled_order(response) -> dict | None:
    """
    Extrae una ejecución confirmada como filled.
    """

    if not isinstance(response, dict):
        return None

    if response.get("status") != "ok":
        return None

    status = _get_first_status(response)

    if status is None:
        return None

    filled = status.get("filled")

    if not isinstance(filled, dict):
        return None

    return filled


def _response_error(response) -> str:
    """
    Devuelve una descripción utilizable de una respuesta fallida.
    """

    if not isinstance(response, dict):
        return repr(response)

    status = _get_first_status(response)

    if status and status.get("error"):
        return str(status["error"])

    return str(response.get("response", response))


def _place_stop_loss(
    asset: str,
    is_buy: bool,
    position_size: float,
    stop_price: float,
):
    """
    Crea un Stop Loss nativo en Hyperliquid.
    """

    close_side = not is_buy

    response = exchange.order(
        name=asset,
        is_buy=close_side,
        sz=position_size,
        limit_px=stop_price,
        reduce_only=True,
        order_type={
            "trigger": {
                "triggerPx": stop_price,
                "isMarket": True,
                "tpsl": "sl",
            }
        },
    )

    print("\n" + "=" * 80)
    print("STOP LOSS RAW RESPONSE")
    pprint.pp(response, sort_dicts=False)
    print("=" * 80 + "\n")

    return response


def _place_take_profit(
    asset: str,
    is_buy: bool,
    position_size: float,
    take_profit_price: float,
):
    """
    Crea un Take Profit nativo en Hyperliquid.
    """

    close_side = not is_buy

    response = exchange.order(
        name=asset,
        is_buy=close_side,
        sz=position_size,
        limit_px=take_profit_price,
        reduce_only=True,
        order_type={
            "trigger": {
                "triggerPx": take_profit_price,
                "isMarket": True,
                "tpsl": "tp",
            }
        },
    )

    print("\n" + "=" * 80)
    print("TAKE PROFIT RAW RESPONSE")
    pprint.pp(response, sort_dicts=False)
    print("=" * 80 + "\n")

    return response


def _cancel_order(
    asset: str,
    order_id: str | None,
) -> str | None:
    """
    Intenta cancelar una orden y devuelve un error si falla.
    """

    if order_id is None:
        return None

    try:
        print(
            f"Cancelling protective order: "
            f"asset={asset} oid={order_id}"
        )

        response = exchange.cancel(
            name=asset,
            oid=int(order_id),
        )

        pprint.pp(response, sort_dicts=False)

        if not isinstance(response, dict):
            return (
                f"Cancellation returned invalid response "
                f"for OID {order_id}: {response!r}"
            )

        if response.get("status") != "ok":
            return (
                f"Cancellation failed for OID {order_id}: "
                f"{_response_error(response)}"
            )

        status = _get_first_status(response)

        if status is not None and status.get("error"):
            return (
                f"Cancellation failed for OID {order_id}: "
                f"{status['error']}"
            )

        return None

    except Exception as exc:
        return (
            f"Cancellation raised for OID {order_id}: "
            f"{exc}"
        )


def _rollback_open_position(
    asset: str,
    exchange_order_id: str,
    entry_price: float,
    stop_loss_order_id: str | None,
    take_profit_order_id: str | None,
    reason: str,
) -> ExecutionResult:
    """
    Cancela protecciones creadas e intenta cerrar la posición.

    Si el cierre queda confirmado, informa que no hay posición abierta.
    Si no puede confirmarse, conserva toda la información necesaria
    para que execution_agent persista la posición real.
    """

    print("\n" + "!" * 80)
    print("PROTECTION FAILURE — STARTING ROLLBACK")
    print(f"asset={asset}")
    print(f"reason={reason}")
    print("!" * 80)

    cleanup_errors: list[str] = []

    sl_cancel_error = _cancel_order(
        asset=asset,
        order_id=stop_loss_order_id,
    )

    if sl_cancel_error:
        cleanup_errors.append(sl_cancel_error)

    tp_cancel_error = _cancel_order(
        asset=asset,
        order_id=take_profit_order_id,
    )

    if tp_cancel_error:
        cleanup_errors.append(tp_cancel_error)

    last_close_response = None

    for attempt in range(3):
        try:
            print(
                f"Rollback close attempt "
                f"{attempt + 1}/3"
            )

            last_close_response = exchange.market_close(
                coin=asset,
            )

            print("\n" + "=" * 80)
            print("MARKET CLOSE RAW RESPONSE")
            pprint.pp(
                last_close_response,
                sort_dicts=False,
            )
            print("=" * 80)

            close_filled = _extract_filled_order(
                last_close_response
            )

            if close_filled is not None:
                error_parts = [
                    reason,
                    "Rollback market close confirmed.",
                ]

                if cleanup_errors:
                    error_parts.append(
                        "Protective-order cleanup warnings: "
                        + " | ".join(cleanup_errors)
                    )

                return ExecutionResult(
                    success=False,
                    position_open=False,
                    exchange_order_id=exchange_order_id,
                    stop_loss_order_id=stop_loss_order_id,
                    take_profit_order_id=take_profit_order_id,
                    entry_price=entry_price,
                    error=" ".join(error_parts),
                )

        except Exception as exc:
            last_close_response = (
                f"{type(exc).__name__}: {exc}"
            )

        if attempt < 2:
            time.sleep(0.5)

    error_parts = [
        reason,
        "Rollback market close could not be confirmed "
        "after 3 attempts. "
        f"Last response: {last_close_response}",
    ]

    if cleanup_errors:
        error_parts.append(
            "Protective-order cleanup warnings: "
            + " | ".join(cleanup_errors)
        )

    return ExecutionResult(
        success=False,
        position_open=True,
        exchange_order_id=exchange_order_id,
        stop_loss_order_id=stop_loss_order_id,
        take_profit_order_id=take_profit_order_id,
        entry_price=entry_price,
        error=" ".join(error_parts),
    )


def execute(
    asset: str,
    direction: str,
    position_size: float,
) -> ExecutionResult:
    """
    Ejecuta una operación completa en Hyperliquid.

    Flujo:

    1. Abrir posición.
    2. Crear Stop Loss nativo.
    3. Crear Take Profit nativo.
    4. Confirmar ambas protecciones.
    5. Si alguna protección falla, ejecutar rollback.
    6. Devolver el estado real de la posición.

    No realiza persistencia en SQLite.
    No envía notificaciones.
    """

    exchange_order_id: str | None = None
    stop_loss_order_id: str | None = None
    take_profit_order_id: str | None = None
    entry_price: float | None = None
    entry_opened = False

    try:
        normalized_direction = direction.upper()

        if normalized_direction not in {"LONG", "SHORT"}:
            return ExecutionResult(
                success=False,
                position_open=False,
                error=f"Unsupported direction: {direction}",
            )

        is_buy = normalized_direction == "LONG"

        info = get_info()

        decimals = next(
            item["szDecimals"]
            for item in info.meta()["universe"]
            if item["name"] == asset
        )

        position_size = round(position_size, decimals)

        if position_size <= 0:
            return ExecutionResult(
                success=False,
                position_open=False,
                error=(
                    f"Invalid rounded position size for {asset}: "
                    f"{position_size}"
                ),
            )

        print(
            f"ASSET={asset} "
            f"SIZE={position_size} "
            f"DECIMALS={decimals}"
        )

        print("\n" + "=" * 80)
        print("AUDIT: market_open()")
        print(f"asset={asset}")
        print(f"direction={normalized_direction}")
        print(f"position_size={position_size}")
        print("=" * 80)

        open_response = exchange.market_open(
            name=asset,
            is_buy=is_buy,
            sz=position_size,
        )

        pprint.pp(open_response, sort_dicts=False)

        filled = _extract_filled_order(open_response)

        if filled is None:
            return ExecutionResult(
                success=False,
                position_open=False,
                error=(
                    "Entry order was not confirmed as filled: "
                    f"{_response_error(open_response)}"
                ),
            )

        if filled.get("oid") is None:
            return ExecutionResult(
                success=False,
                position_open=False,
                error=(
                    "Entry response was filled but contained no OID: "
                    f"{filled}"
                ),
            )

        if filled.get("avgPx") is None:
            return ExecutionResult(
                success=False,
                position_open=False,
                error=(
                    "Entry response was filled but contained no avgPx: "
                    f"{filled}"
                ),
            )

        exchange_order_id = str(filled["oid"])
        entry_price = float(filled["avgPx"])
        entry_opened = True

        print("FILLED:", filled)

        stop_loss = calculate_stop_loss(
            entry_price,
            normalized_direction,
        )

        take_profit = calculate_take_profit(
            entry_price,
            normalized_direction,
        )

        sl_response = _place_stop_loss(
            asset=asset,
            is_buy=is_buy,
            position_size=position_size,
            stop_price=stop_loss,
        )

        stop_loss_order_id = _extract_resting_order_id(
            sl_response
        )

        if stop_loss_order_id is None:
            return _rollback_open_position(
                asset=asset,
                exchange_order_id=exchange_order_id,
                entry_price=entry_price,
                stop_loss_order_id=None,
                take_profit_order_id=None,
                reason=(
                    "Stop Loss was not confirmed as resting: "
                    f"{_response_error(sl_response)}"
                ),
            )

        tp_response = _place_take_profit(
            asset=asset,
            is_buy=is_buy,
            position_size=position_size,
            take_profit_price=take_profit,
        )

        take_profit_order_id = _extract_resting_order_id(
            tp_response
        )

        if take_profit_order_id is None:
            return _rollback_open_position(
                asset=asset,
                exchange_order_id=exchange_order_id,
                entry_price=entry_price,
                stop_loss_order_id=stop_loss_order_id,
                take_profit_order_id=None,
                reason=(
                    "Take Profit was not confirmed as resting: "
                    f"{_response_error(tp_response)}"
                ),
            )

        return ExecutionResult(
            success=True,
            position_open=True,
            exchange_order_id=exchange_order_id,
            stop_loss_order_id=stop_loss_order_id,
            take_profit_order_id=take_profit_order_id,
            entry_price=entry_price,
            error=None,
        )

    except Exception as exc:
        if (
            entry_opened
            and exchange_order_id is not None
            and entry_price is not None
        ):
            return _rollback_open_position(
                asset=asset,
                exchange_order_id=exchange_order_id,
                entry_price=entry_price,
                stop_loss_order_id=stop_loss_order_id,
                take_profit_order_id=take_profit_order_id,
                reason=(
                    "Exception after entry was filled: "
                    f"{exc}"
                ),
            )

        return ExecutionResult(
            success=False,
            position_open=False,
            error=str(exc),
        )
