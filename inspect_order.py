from pprint import pprint

from hyperliquid_client import get_info

from hyperliquid_poc.config import ACCOUNT_ADDRESS

OID = 498039820656

info = get_info()

result = info.query_order_by_oid(
    ACCOUNT_ADDRESS,
    OID,
)

print(type(result))
print()
pprint(result)
