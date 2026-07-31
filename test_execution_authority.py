from execution_authority import can_execute_live
from execution_workflow import execute


print()
print("LIVE AUTHORITY TEST")
print("=" * 60)

print("AUTH:", can_execute_live())

result = execute(
    asset="BTC",
    direction="LONG",
    position_size=0.001,
)

print()
print("RESULT:")
print(result)

print()
print("SUCCESS:", result.success)
print("ORDER:", result.exchange_order_id)
print("ERROR:", result.error)
