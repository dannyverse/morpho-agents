from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum

from margin_admission import (
    AccountEnvironment,
    AccountNormalizationStatus,
    AccountSnapshotV1,
    AccountSource,
    MarginMode,
)


class SnapshotNormalizationErrorCode(Enum):
    ACCOUNT_STATE_UNAVAILABLE = "ACCOUNT_STATE_UNAVAILABLE"
    ACCOUNT_STATE_INVALID = "ACCOUNT_STATE_INVALID"
    MARGIN_SUMMARY_MISSING = "MARGIN_SUMMARY_MISSING"
    ACCOUNT_VALUE_MISSING = "ACCOUNT_VALUE_MISSING"
    ACCOUNT_VALUE_INVALID = "ACCOUNT_VALUE_INVALID"
    TOTAL_MARGIN_USED_MISSING = "TOTAL_MARGIN_USED_MISSING"
    TOTAL_MARGIN_USED_INVALID = "TOTAL_MARGIN_USED_INVALID"
    WITHDRAWABLE_MISSING = "WITHDRAWABLE_MISSING"
    WITHDRAWABLE_INVALID = "WITHDRAWABLE_INVALID"
    EXCHANGE_TIMESTAMP_MISSING = "EXCHANGE_TIMESTAMP_MISSING"
    EXCHANGE_TIMESTAMP_INVALID = "EXCHANGE_TIMESTAMP_INVALID"
    ASSET_POSITIONS_MISSING = "ASSET_POSITIONS_MISSING"
    ASSET_POSITIONS_INVALID = "ASSET_POSITIONS_INVALID"
    ASSET_POSITION_INVALID = "ASSET_POSITION_INVALID"


@dataclass(frozen=True)
class AccountPositionSnapshotV1:
    asset: str
    signed_size: Decimal
    position_value: Decimal
    margin_used: Decimal
    margin_mode: MarginMode
    leverage: Decimal | None
    unrealized_pnl: Decimal | None
    entry_price: Decimal | None
    liquidation_price: Decimal | None


def get_account_snapshot() -> AccountSnapshotV1:
    account_address = _get_account_address()

    received_at = datetime.now(timezone.utc)
    errors: list[str] = []

    try:
        account_state = _get_account_state()
    except Exception:
        account_state = None
        errors.append(
            SnapshotNormalizationErrorCode.ACCOUNT_STATE_UNAVAILABLE.value
        )

    if not isinstance(account_state, dict):
        if not errors:
            errors.append(
                SnapshotNormalizationErrorCode.ACCOUNT_STATE_INVALID.value
            )
        return _invalid_snapshot(
            received_at=received_at,
            errors=errors,
            account_address=account_address,
        )


    margin_summary = account_state.get("marginSummary")
    if not isinstance(margin_summary, dict):
        errors.append(
            SnapshotNormalizationErrorCode.MARGIN_SUMMARY_MISSING.value
        )
        margin_summary = {}

    account_value = _required_non_negative_decimal(
        container=margin_summary,
        field="accountValue",
        missing_code=SnapshotNormalizationErrorCode.ACCOUNT_VALUE_MISSING,
        invalid_code=SnapshotNormalizationErrorCode.ACCOUNT_VALUE_INVALID,
        errors=errors,
    )
    total_margin_used = _required_non_negative_decimal(
        container=margin_summary,
        field="totalMarginUsed",
        missing_code=(
            SnapshotNormalizationErrorCode.TOTAL_MARGIN_USED_MISSING
        ),
        invalid_code=(
            SnapshotNormalizationErrorCode.TOTAL_MARGIN_USED_INVALID
        ),
        errors=errors,
    )
    withdrawable = _required_non_negative_decimal(
        container=account_state,
        field="withdrawable",
        missing_code=SnapshotNormalizationErrorCode.WITHDRAWABLE_MISSING,
        invalid_code=SnapshotNormalizationErrorCode.WITHDRAWABLE_INVALID,
        errors=errors,
    )
    exchange_timestamp = _exchange_timestamp(
        account_state=account_state,
        received_at=received_at,
        errors=errors,
    )
    asset_positions = _asset_positions(
        account_state=account_state,
        errors=errors,
    )

    status = (
        AccountNormalizationStatus.VALID
        if not errors
        else AccountNormalizationStatus.INVALID
    )
    snapshot_id = (
        f"{account_address}:"
        f"{int(exchange_timestamp.timestamp() * 1000)}"
    )

    return AccountSnapshotV1(
        schema_version="1.0",
        snapshot_id=snapshot_id,
        account_address=account_address,
        environment=AccountEnvironment.MAINNET,
        source=AccountSource.HYPERLIQUID_CLEARINGHOUSE_STATE,
        exchange_timestamp=exchange_timestamp,
        received_at=received_at,
        account_value=account_value,
        total_margin_used=total_margin_used,
        withdrawable=withdrawable,
        asset_positions=asset_positions,
        normalization_status=status,
        normalization_errors=tuple(errors),
    )


def _invalid_snapshot(
    received_at: datetime,
    errors: list[str],
    account_address: str,
) -> AccountSnapshotV1:
    return AccountSnapshotV1(
        schema_version="1.0",
        snapshot_id=(
            f"{account_address}:invalid:{received_at.isoformat()}"
        ),
        account_address=account_address,
        environment=AccountEnvironment.MAINNET,
        source=AccountSource.HYPERLIQUID_CLEARINGHOUSE_STATE,
        exchange_timestamp=received_at,
        received_at=received_at,
        account_value=Decimal("0"),
        total_margin_used=Decimal("0"),
        withdrawable=Decimal("0"),
        asset_positions=(),
        normalization_status=AccountNormalizationStatus.INVALID,
        normalization_errors=tuple(errors),
    )


def _required_non_negative_decimal(
    container: dict,
    field: str,
    missing_code: SnapshotNormalizationErrorCode,
    invalid_code: SnapshotNormalizationErrorCode,
    errors: list[str],
) -> Decimal:
    if field not in container or container.get(field) is None:
        errors.append(missing_code.value)
        return Decimal("0")

    value = _decimal(container.get(field))
    if value is None or value < 0:
        errors.append(invalid_code.value)
        return Decimal("0")

    return value


def _exchange_timestamp(
    account_state: dict,
    received_at: datetime,
    errors: list[str],
) -> datetime:
    if "time" not in account_state or account_state.get("time") is None:
        errors.append(
            SnapshotNormalizationErrorCode.EXCHANGE_TIMESTAMP_MISSING.value
        )
        return received_at

    milliseconds = _decimal(account_state.get("time"))
    if milliseconds is None or milliseconds < 0:
        errors.append(
            SnapshotNormalizationErrorCode.EXCHANGE_TIMESTAMP_INVALID.value
        )
        return received_at

    try:
        return datetime.fromtimestamp(
            float(milliseconds / Decimal("1000")),
            tz=timezone.utc,
        )
    except (OverflowError, OSError, ValueError):
        errors.append(
            SnapshotNormalizationErrorCode.EXCHANGE_TIMESTAMP_INVALID.value
        )
        return received_at


def _asset_positions(
    account_state: dict,
    errors: list[str],
) -> tuple[AccountPositionSnapshotV1, ...]:
    if "assetPositions" not in account_state:
        errors.append(
            SnapshotNormalizationErrorCode.ASSET_POSITIONS_MISSING.value
        )
        return ()

    raw_positions = account_state.get("assetPositions")
    if not isinstance(raw_positions, list):
        errors.append(
            SnapshotNormalizationErrorCode.ASSET_POSITIONS_INVALID.value
        )
        return ()

    normalized_positions = []

    for index, item in enumerate(raw_positions):
        position = item.get("position") if isinstance(item, dict) else None
        normalized = _asset_position(position)

        if normalized is None:
            errors.append(
                f"{SnapshotNormalizationErrorCode.ASSET_POSITION_INVALID.value}:"
                f"{index}"
            )
            continue

        if normalized.signed_size != 0:
            normalized_positions.append(normalized)

    return tuple(normalized_positions)


def _asset_position(position: object) -> AccountPositionSnapshotV1 | None:
    if not isinstance(position, dict):
        return None

    asset = position.get("coin")
    signed_size = _decimal(position.get("szi"))
    position_value = _decimal(position.get("positionValue"))
    margin_used = _decimal(position.get("marginUsed"))

    if (
        not isinstance(asset, str)
        or not asset
        or signed_size is None
        or position_value is None
        or position_value < 0
        or margin_used is None
        or margin_used < 0
    ):
        return None

    leverage_data = position.get("leverage")
    margin_mode = MarginMode.UNKNOWN
    leverage = None

    if isinstance(leverage_data, dict):
        leverage_type = leverage_data.get("type")
        if leverage_type == "cross":
            margin_mode = MarginMode.CROSS
        elif leverage_type == "isolated":
            margin_mode = MarginMode.ISOLATED
        leverage = _optional_positive_decimal(leverage_data.get("value"))

    return AccountPositionSnapshotV1(
        asset=asset,
        signed_size=signed_size,
        position_value=position_value,
        margin_used=margin_used,
        margin_mode=margin_mode,
        leverage=leverage,
        unrealized_pnl=_optional_decimal(position.get("unrealizedPnl")),
        entry_price=_optional_positive_decimal(position.get("entryPx")),
        liquidation_price=_optional_positive_decimal(
            position.get("liquidationPx")
        ),
    )


def _decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None

    if not decimal_value.is_finite():
        return None

    return decimal_value


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value)


def _optional_positive_decimal(value: object) -> Decimal | None:
    decimal_value = _optional_decimal(value)
    if decimal_value is None or decimal_value <= 0:
        return None
    return decimal_value

def _get_account_state():
    from hyperliquid_client import get_account_state
    return get_account_state()

def _get_account_address():
    from hyperliquid_poc.config import ACCOUNT_ADDRESS
    return ACCOUNT_ADDRESS
