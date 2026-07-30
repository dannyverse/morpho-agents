import time

from hyperliquid_client import (
    get_exchange,
    get_account_state,
)


WAIT_SECONDS = 30

def get_open_assets():

    state = get_account_state()

    positions = state.get(
        "assetPositions",
        []
    )

    assets = []

    for item in positions:

        position = item.get("position", {})

        coin = position.get("coin")
        szi = position.get("szi")

        if szi and float(szi) != 0:
            assets.append(coin)

    return assets


def main():

    exchange = get_exchange()

    assets = get_open_assets()

    print()
    print("=" * 60)
    print("CONTROLLED EXCHANGE POSITION CLEANUP")
    print("=" * 60)
    print(f"Positions detected: {len(assets)}")
    print()

    closed = []
    failed = []

    for index, asset in enumerate(assets, start=1):

        print(
            f"[{index}/{len(assets)}] Closing {asset}"
        )

        try:

            response = exchange.market_close(
                coin=asset
            )

            print(response)

            if response.get("status") == "ok":

                closed.append(asset)

                print(
                    f"✅ CLOSED {asset}"
                )

            else:

                failed.append(asset)

                print(
                    f"⚠️ FAILED {asset}"
                )

        except Exception as e:

            failed.append(asset)

            print(
                f"❌ ERROR {asset}: {e}"
            )

        print(
            f"Waiting {WAIT_SECONDS}s..."
        )

        time.sleep(
            WAIT_SECONDS
        )


    print()
    print("=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)

    print(
        f"Closed: {len(closed)}"
    )

    print(closed)

    print()

    print(
        f"Failed: {len(failed)}"
    )

    print(failed)


if __name__ == "__main__":
    main()
