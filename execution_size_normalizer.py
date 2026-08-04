from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from enum import Enum


MAX_SIZE_DECIMALS = 18


class NormalizationStatus(Enum):
    NORMALIZED = "NORMALIZED"
    INVALID_SIZE = "INVALID_SIZE"
    INVALID_PRECISION = "INVALID_PRECISION"
    SIZE_ROUNDED_TO_ZERO = "SIZE_ROUNDED_TO_ZERO"
    UNSUPPORTED_ROUNDING_POLICY = "UNSUPPORTED_ROUNDING_POLICY"


class ReasonCode(Enum):
    SIZE_ALREADY_NORMALIZED = "SIZE_ALREADY_NORMALIZED"
    SIZE_TRUNCATED_TO_PRECISION = "SIZE_TRUNCATED_TO_PRECISION"
    SIZE_IS_ZERO = "SIZE_IS_ZERO"
    SIZE_IS_NEGATIVE = "SIZE_IS_NEGATIVE"
    SIZE_IS_NOT_FINITE = "SIZE_IS_NOT_FINITE"
    SIZE_TYPE_INVALID = "SIZE_TYPE_INVALID"
    PRECISION_IS_NEGATIVE = "PRECISION_IS_NEGATIVE"
    PRECISION_IS_NOT_INTEGER = "PRECISION_IS_NOT_INTEGER"
    PRECISION_OUT_OF_RANGE = "PRECISION_OUT_OF_RANGE"
    PRECISION_TYPE_INVALID = "PRECISION_TYPE_INVALID"
    SIZE_BELOW_PRECISION_QUANTUM = "SIZE_BELOW_PRECISION_QUANTUM"
    ROUNDING_POLICY_NOT_SUPPORTED = "ROUNDING_POLICY_NOT_SUPPORTED"


class RoundingPolicy(Enum):
    TRUNCATE_TOWARD_ZERO = "TRUNCATE_TOWARD_ZERO"
    ROUND_TO_NEAREST = "ROUND_TO_NEAREST"
    ROUND_UP = "ROUND_UP"


@dataclass(frozen=True)
class ExecutionSizeNormalizationResult:
    schema_version: str
    status: NormalizationStatus
    reason_code: ReasonCode
    raw_size: Decimal | None
    normalized_size: Decimal | None
    size_decimals: int | None
    size_quantum: Decimal | None
    adjustment: Decimal | None
    rounding_policy: RoundingPolicy
    was_changed: bool


def normalize_execution_size(
    raw_size: Decimal,
    size_decimals: int,
    rounding_policy: RoundingPolicy = RoundingPolicy.TRUNCATE_TOWARD_ZERO,
) -> ExecutionSizeNormalizationResult:
    if rounding_policy is not RoundingPolicy.TRUNCATE_TOWARD_ZERO:
        return ExecutionSizeNormalizationResult(
            schema_version="1.0",
            status=NormalizationStatus.UNSUPPORTED_ROUNDING_POLICY,
            reason_code=ReasonCode.ROUNDING_POLICY_NOT_SUPPORTED,
            raw_size=raw_size if isinstance(raw_size, Decimal) else None,
            normalized_size=None,
            size_decimals=(
                size_decimals
                if isinstance(size_decimals, int)
                and not isinstance(size_decimals, bool)
                else None
            ),
            size_quantum=None,
            adjustment=None,
            rounding_policy=rounding_policy,
            was_changed=False,
        )

    if isinstance(size_decimals, bool) or size_decimals is None:
        return _invalid_precision(
            raw_size=raw_size,
            size_decimals=None,
            reason_code=ReasonCode.PRECISION_TYPE_INVALID,
            rounding_policy=rounding_policy,
        )

    if not isinstance(size_decimals, int):
        reason_code = (
            ReasonCode.PRECISION_IS_NOT_INTEGER
            if isinstance(size_decimals, Decimal)
            and size_decimals.is_finite()
            and size_decimals != size_decimals.to_integral_value()
            else ReasonCode.PRECISION_TYPE_INVALID
        )
        return _invalid_precision(
            raw_size=raw_size,
            size_decimals=None,
            reason_code=reason_code,
            rounding_policy=rounding_policy,
        )

    if size_decimals < 0:
        return _invalid_precision(
            raw_size=raw_size,
            size_decimals=size_decimals,
            reason_code=ReasonCode.PRECISION_IS_NEGATIVE,
            rounding_policy=rounding_policy,
        )

    if size_decimals > MAX_SIZE_DECIMALS:
        return _invalid_precision(
            raw_size=raw_size,
            size_decimals=size_decimals,
            reason_code=ReasonCode.PRECISION_OUT_OF_RANGE,
            rounding_policy=rounding_policy,
        )

    size_quantum = Decimal(1).scaleb(-size_decimals)

    if not isinstance(raw_size, Decimal) or isinstance(raw_size, bool):
        return _invalid_size(
            raw_size=None,
            size_decimals=size_decimals,
            size_quantum=size_quantum,
            reason_code=ReasonCode.SIZE_TYPE_INVALID,
            rounding_policy=rounding_policy,
        )

    if not raw_size.is_finite():
        return _invalid_size(
            raw_size=None,
            size_decimals=size_decimals,
            size_quantum=size_quantum,
            reason_code=ReasonCode.SIZE_IS_NOT_FINITE,
            rounding_policy=rounding_policy,
        )

    if raw_size == 0:
        return _invalid_size(
            raw_size=raw_size,
            size_decimals=size_decimals,
            size_quantum=size_quantum,
            reason_code=ReasonCode.SIZE_IS_ZERO,
            rounding_policy=rounding_policy,
        )

    if raw_size < 0:
        return _invalid_size(
            raw_size=raw_size,
            size_decimals=size_decimals,
            size_quantum=size_quantum,
            reason_code=ReasonCode.SIZE_IS_NEGATIVE,
            rounding_policy=rounding_policy,
        )

    normalized_size = raw_size.quantize(
        size_quantum,
        rounding=ROUND_DOWN,
    )

    if normalized_size == 0:
        return ExecutionSizeNormalizationResult(
            schema_version="1.0",
            status=NormalizationStatus.SIZE_ROUNDED_TO_ZERO,
            reason_code=ReasonCode.SIZE_BELOW_PRECISION_QUANTUM,
            raw_size=raw_size,
            normalized_size=None,
            size_decimals=size_decimals,
            size_quantum=size_quantum,
            adjustment=raw_size,
            rounding_policy=rounding_policy,
            was_changed=True,
        )

    was_changed = normalized_size != raw_size

    return ExecutionSizeNormalizationResult(
        schema_version="1.0",
        status=NormalizationStatus.NORMALIZED,
        reason_code=(
            ReasonCode.SIZE_TRUNCATED_TO_PRECISION
            if was_changed
            else ReasonCode.SIZE_ALREADY_NORMALIZED
        ),
        raw_size=raw_size,
        normalized_size=normalized_size,
        size_decimals=size_decimals,
        size_quantum=size_quantum,
        adjustment=raw_size - normalized_size,
        rounding_policy=rounding_policy,
        was_changed=was_changed,
    )


def _invalid_precision(
    raw_size: object,
    size_decimals: int | None,
    reason_code: ReasonCode,
    rounding_policy: RoundingPolicy,
) -> ExecutionSizeNormalizationResult:
    return ExecutionSizeNormalizationResult(
        schema_version="1.0",
        status=NormalizationStatus.INVALID_PRECISION,
        reason_code=reason_code,
        raw_size=raw_size if isinstance(raw_size, Decimal) else None,
        normalized_size=None,
        size_decimals=size_decimals,
        size_quantum=None,
        adjustment=None,
        rounding_policy=rounding_policy,
        was_changed=False,
    )


def _invalid_size(
    raw_size: Decimal | None,
    size_decimals: int,
    size_quantum: Decimal,
    reason_code: ReasonCode,
    rounding_policy: RoundingPolicy,
) -> ExecutionSizeNormalizationResult:
    return ExecutionSizeNormalizationResult(
        schema_version="1.0",
        status=NormalizationStatus.INVALID_SIZE,
        reason_code=reason_code,
        raw_size=raw_size,
        normalized_size=None,
        size_decimals=size_decimals,
        size_quantum=size_quantum,
        adjustment=None,
        rounding_policy=rounding_policy,
        was_changed=False,
    )
