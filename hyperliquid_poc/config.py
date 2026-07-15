import os

from dotenv import load_dotenv
from eth_account import Account

load_dotenv()

API_PRIVATE_KEY = os.getenv("HL_API_PRIVATE_KEY")
ACCOUNT_ADDRESS = os.getenv("HL_ACCOUNT_ADDRESS")

if not API_PRIVATE_KEY:
    raise Exception("HL_API_PRIVATE_KEY not configured")

if not ACCOUNT_ADDRESS:
    raise Exception("HL_ACCOUNT_ADDRESS not configured")

API_WALLET = Account.from_key(API_PRIVATE_KEY)
