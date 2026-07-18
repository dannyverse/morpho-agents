from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

from hyperliquid_poc.config import (
    API_WALLET,
    ACCOUNT_ADDRESS,
)

_exchange = None
_info = None


def get_exchange():
    global _exchange

    if _exchange is None:
        _exchange = Exchange(
            wallet=API_WALLET,
            account_address=ACCOUNT_ADDRESS,
        )

    return _exchange


def get_info():
    global _info

    if _info is None:
        _info = Info(skip_ws=True)

    return _info

def get_account_state():
    """
    Devuelve el estado completo de la cuenta en Hyperliquid.
    Fuente primaria de verdad para el reconciliador.
    """
    info = get_info()
    return info.user_state(ACCOUNT_ADDRESS)

def get_order(order_id):
    info = get_info()

    print(f"OID={order_id!r} TYPE={type(order_id)}")

    return info.query_order_by_oid(
        ACCOUNT_ADDRESS,
        int(order_id),
    )
