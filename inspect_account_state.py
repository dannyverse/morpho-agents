from pprint import pprint

from hyperliquid_client import get_account_state

state = get_account_state()

pprint(state)
