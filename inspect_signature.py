import inspect

from hyperliquid_client import get_info

info = get_info()

print(inspect.signature(info.query_order_by_oid))
