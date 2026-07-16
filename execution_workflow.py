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

from hyperliquid.exchange import Exchange

from hyperliquid_poc.config import (
    API_WALLET,
    ACCOUNT_ADDRESS,
)


exchange = Exchange(
    wallet=API_WALLET,
    account_address=ACCOUNT_ADDRESS,
)


@dataclass
class ExecutionResult:
    success: bool
    exchange_order_id: str | None = None
    entry_price: float | None = None
    error: str | None = None


def execute(
    asset: str,
    direction: str,
    position_size: float,
) -> ExecutionResult:
    """
    Ejecuta una orden de mercado en Hyperliquid.

    De momento únicamente abre la posición y devuelve
    la información básica de ejecución.

    En siguientes iteraciones añadiremos:

    - Esperar confirmación
    - Stop Loss nativo
    - Take Profit nativo
    - Verificación final
    """

    try:

        is_buy = direction.upper() == "LONG"

        result = exchange.market_open(
            name=asset,
            is_buy=is_buy,
            sz=position_size,
        )

        print(result)

        filled = result["response"]["data"]["statuses"][0]["filled"]

        return ExecutionResult(
            success=True,
            exchange_order_id=str(filled["oid"]),
            entry_price=float(filled["avgPx"]),
        )

    except Exception as e:

        return ExecutionResult(
            success=False,
            error=str(e),
        )
