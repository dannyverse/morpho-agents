from hyperliquid_client import get_account_state


def main():

    state = get_account_state()

    positions = state.get(
        "assetPositions",
        []
    )

    print()
    print("=" * 60)
    print("EXCHANGE OPEN POSITIONS")
    print("=" * 60)

    count = 0

    for item in positions:

        position = item.get("position", {})

        coin = position.get("coin")
        szi = position.get("szi")

        if szi and float(szi) != 0:

            count += 1

            print(
                f"{coin:10} "
                f"szi={szi:>12} "
                f"value={position.get('positionValue')} "
                f"entry={position.get('entryPx')}"
            )

    print()
    print(f"TOTAL: {count}")


if __name__ == "__main__":
    main()
