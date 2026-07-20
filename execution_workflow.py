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

from hyperliquid_client import get_exchange


from positions import (
    calculate_stop_loss,
    calculate_take_profit,
)

exchange = get_exchange()

@dataclass
class ExecutionResult:
    success: bool
    exchange_order_id: str | None = None
    stop_loss_order_id: str | None = None
    take_profit_order_id: str | None = None
    entry_price: float | None = None
    error: str | None = None

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

    return exchange.order(
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

    return exchange.order(
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

def _extract_resting_order_id(response) -> str | None:

    try:
        statuses = response["response"]["data"]["statuses"]

        if statuses and "resting" in statuses[0]:
            return str(statuses[0]["resting"]["oid"])

    except Exception:
        pass

    return None    

def execute(
    asset: str,
    direction: str,
    position_size: float,
) -> ExecutionResult:

    """
    Ejecuta una operación completa en Hyperliquid.

    Flujo previsto:

    1. Abrir posición.
    2. Crear Stop Loss nativo.
    3. Crear Take Profit nativo.
    4. Verificar la ejecución.
    5. Devolver ExecutionResult.

    No realiza persistencia en SQLite.
    No envía notificaciones.
    """

    try:

        is_buy = direction.upper() == "LONG"

        from hyperliquid_client import get_info

        info = get_info()

        decimals = next(
            item["szDecimals"]
            for item in info.meta()["universe"]
            if item["name"] == asset
        )

        position_size = round(position_size, decimals)

        print(f"ASSET={asset} SIZE={position_size} DECIMALS={decimals}")

        result = exchange.market_open(
            name=asset,
            is_buy=is_buy,
            sz=position_size,
        )

        import pprint
        pprint.pp(result, sort_dicts=False)

        if result.get("status") != "ok":
            return ExecutionResult(
                success=False,
                error=str(result.get("response")),
            )

        status = result["response"]["data"]["statuses"][0]

        if "error" in status:
            return ExecutionResult(
                success=False,
                error=status["error"],
            )

        filled = status["filled"]
        entry_price = float(filled["avgPx"])

        stop_loss = calculate_stop_loss(
            entry_price,
            direction,
        )

        stop_loss = calculate_stop_loss(
            entry_price,
            direction,
        )

        take_profit = calculate_take_profit(
            entry_price,
            direction,
        )

        sl_result = _place_stop_loss(
            asset=asset,
            is_buy=is_buy,
            position_size=position_size,
            stop_price=stop_loss,
        )

        print(sl_result)

        stop_loss_order_id = _extract_resting_order_id(sl_result)

        tp_result = _place_take_profit(
            asset=asset,
            is_buy=is_buy,
            position_size=position_size,
            take_profit_price=take_profit,
        )

        print(tp_result)

        take_profit_order_id = _extract_resting_order_id(tp_result)

        return ExecutionResult(
            success=True,
            exchange_order_id=str(filled["oid"]),
            stop_loss_order_id=stop_loss_order_id,
            take_profit_order_id=take_profit_order_id,
            entry_price=entry_price,
        )

    except Exception as e:

        return ExecutionResult(
            success=False,
            error=str(e),
        )
