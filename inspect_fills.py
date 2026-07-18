from pprint import pprint

from hyperliquid_client import get_info
from hyperliquid_poc.config import ACCOUNT_ADDRESS

info = get_info()

fills = info.user_fills(ACCOUNT_ADDRESS)

print(type(fills))
print()

pprint(fills)
