import sqlite3

from hyperliquid_client import get_exchange
from positions import close_position
from hyperliquid_client import get_info
from hyperliquid_poc.config import ACCOUNT_ADDRESS


DB = "trading_system.db"


def main():

    conn = sqlite3.connect(DB)

    rows = conn.execute(
        """
        SELECT
            position_id,
            asset,
            direction,
            position_size
        FROM positions
        WHERE status='OPEN'
        """
    ).fetchall()

    print()
    print("=" * 60)
    print("CLOSING LEGACY POSITIONS")
    print("=" * 60)
    print(f"Positions found: {len(rows)}")
    print()

    exchange = get_exchange()
    info = get_info()

    for (
        position_id,
        asset,
        direction,
        size,
    ) in rows:

        print(
            f"Closing {asset} {direction} size={size}"
        )

        try:

            response = exchange.market_close(
                coin=asset
            )

            print(response)

            close_position(
                conn,
                position_id,
                0.0
            )

            print(
                f"✅ CLOSED {asset}"
            )

        except Exception as e:

            print(
                f"❌ FAILED {asset}: {e}"
            )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
