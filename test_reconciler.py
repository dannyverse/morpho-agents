import sqlite3

from exchange_reconciler import reconcile

conn = sqlite3.connect("trading_system.db")

result = reconcile(conn)

print()
print("RESULT:", result)

conn.close()
