from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AccountEnvironment(Enum):
    MAINNET = "MAINNET"
    TESTNET = "TESTNET"


class AccountNormalizationStatus(Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class AccountSource(Enum):
    HYPERLIQUID_CLEARINGHOUSE_STATE = (
        "HYPERLIQUID_CLEARINGHOUSE_STATE"
    )


class AdmissionDecision(Enum):
    ADMITTED = "ADMITTED"
    INSUFFICIENT_MARGIN = "INSUFFICIENT_MARGIN"
    ACCOUNT_UNKNOWN = "ACCOUNT_UNKNOWN"
    STALE_DATA = "STALE_DATA"
    INVALID_CANDIDATE = "INVALID_CANDIDATE"
    UNSUPPORTED_MARGIN_MODE = "UNSUPPORTED_MARGIN_MODE"


class AdmissionReasonCode(Enum):
    CAPACITY_SUFFICIENT = "CAPACITY_SUFFICIENT"
    CAPACITY_BELOW_REQUIREMENT = "CAPACITY_BELOW_REQUIREMENT"
    SNAPSHOT_MISSING = "SNAPSHOT_MISSING"
    SNAPSHOT_INVALID = "SNAPSHOT_INVALID"
    SNAPSHOT_TOO_OLD = "SNAPSHOT_TOO_OLD"
    INVALID_SIZE = "INVALID_SIZE"
    INVALID_PRICE = "INVALID_PRICE"
    INVALID_NOTIONAL = "INVALID_NOTIONAL"
    NOTIONAL_MISMATCH = "NOTIONAL_MISMATCH"
    CYCLE_ID_MISMATCH = "CYCLE_ID_MISMATCH"
    SNAPSHOT_ID_MISMATCH = "SNAPSHOT_ID_MISMATCH"
    SIZE_NOT_NORMALIZED = "SIZE_NOT_NORMALIZED"
    MARGIN_MODE_NOT_SUPPORTED = "MARGIN_MODE_NOT_SUPPORTED"
    INVALID_CYCLE_CONTEXT = "INVALID_CYCLE_CONTEXT"
    INVALID_POLICY = "INVALID_POLICY"
    INVALID_DIRECTION = "INVALID_DIRECTION"
    REDUCE_ONLY_NOT_SUPPORTED = "REDUCE_ONLY_NOT_SUPPORTED"


class CandidateSizeStatus(Enum):
    NORMALIZED = "NORMALIZED"
    UNNORMALIZED = "UNNORMALIZED"


class MarginMode(Enum):
    CROSS = "CROSS"
    ISOLATED = "ISOLATED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class AccountSnapshotV1:
    schema_version: str
    snapshot_id: str
    account_address: str
    environment: AccountEnvironment
    source: AccountSource
    exchange_timestamp: datetime
    received_at: datetime
    account_value: Decimal
    total_margin_used: Decimal
    withdrawable: Decimal
    asset_positions: tuple
    normalization_status: AccountNormalizationStatus
    normalization_errors: tuple[str, ...]


@dataclass(frozen=True)
class CandidateOrderV1:
    schema_version: str
    candidate_id: str
    cycle_id: str
    created_at: datetime
    asset: str
    direction: str
    requested_size: Decimal
    reference_price: Decimal
    reference_price_timestamp: datetime
    requested_notional: Decimal
    margin_mode: MarginMode
    reduce_only: bool
    size_normalization_status: CandidateSizeStatus


@dataclass(frozen=True)
class CycleContextV1:
    schema_version: str
    cycle_id: str
    account_snapshot_id: str
    account_refresh_sequence: int
    reserved_capacity: Decimal
    evaluated_candidates: int
    pending_candidate_ids: tuple[str, ...]
    execution_blocked: bool
    block_reason: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AdmissionPolicyV1:
    schema_version: str
    max_snapshot_age_seconds: Decimal
    absolute_reserve: Decimal
    safety_buffer: Decimal
    supported_margin_mode: MarginMode
    notional_tolerance: Decimal


@dataclass(frozen=True)
class AdmissionResultV1:
    schema_version: str
    decision: AdmissionDecision
    reason_code: AdmissionReasonCode
    candidate_id: str | None
    cycle_id: str | None
    snapshot_id: str | None
    account_refresh_sequence: int | None
    evaluated_at: datetime | None
    snapshot_age_seconds: Decimal | None
    account_value: Decimal | None
    total_margin_used: Decimal | None
    withdrawable: Decimal | None
    reserved_capacity: Decimal
    absolute_reserve: Decimal
    safety_buffer: Decimal
    usable_capacity: Decimal | None
    requested_size: Decimal | None
    reference_price: Decimal | None
    candidate_notional: Decimal | None
    candidate_requirement: Decimal | None
    reservation_amount: Decimal
    remaining_capacity: Decimal | None
    validation_errors: tuple[str, ...]


def evaluate_margin_admission(
    account_snapshot: AccountSnapshotV1 | None,
    candidate_order: CandidateOrderV1,
    cycle_context: CycleContextV1,
    policy: AdmissionPolicyV1,
) -> AdmissionResultV1:
    policy_errors = _validate_policy(policy)
    if policy_errors:
        return _result(
            decision=AdmissionDecision.ACCOUNT_UNKNOWN,
            reason_code=AdmissionReasonCode.INVALID_POLICY,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            validation_errors=policy_errors,
        )

    context_errors = _validate_cycle_context(cycle_context)
    if context_errors:
        return _result(
            decision=AdmissionDecision.INVALID_CANDIDATE,
            reason_code=AdmissionReasonCode.INVALID_CYCLE_CONTEXT,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            validation_errors=context_errors,
        )

    if account_snapshot is None:
        return _result(
            decision=AdmissionDecision.ACCOUNT_UNKNOWN,
            reason_code=AdmissionReasonCode.SNAPSHOT_MISSING,
            account_snapshot=None,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            validation_errors=("account snapshot is missing",),
        )

    snapshot_errors = _validate_account_snapshot(account_snapshot)
    if snapshot_errors:
        return _result(
            decision=AdmissionDecision.ACCOUNT_UNKNOWN,
            reason_code=AdmissionReasonCode.SNAPSHOT_INVALID,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            validation_errors=snapshot_errors,
        )

    if cycle_context.account_snapshot_id != account_snapshot.snapshot_id:
        return _result(
            decision=AdmissionDecision.INVALID_CANDIDATE,
            reason_code=AdmissionReasonCode.SNAPSHOT_ID_MISMATCH,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            validation_errors=("account snapshot id mismatch",),
        )

    snapshot_age = _seconds_between(
        cycle_context.updated_at,
        account_snapshot.exchange_timestamp,
    )

    if snapshot_age < 0:
        return _result(
            decision=AdmissionDecision.ACCOUNT_UNKNOWN,
            reason_code=AdmissionReasonCode.SNAPSHOT_INVALID,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            snapshot_age_seconds=snapshot_age,
            validation_errors=("snapshot timestamp is in the future",),
        )

    if snapshot_age > policy.max_snapshot_age_seconds:
        return _result(
            decision=AdmissionDecision.STALE_DATA,
            reason_code=AdmissionReasonCode.SNAPSHOT_TOO_OLD,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            snapshot_age_seconds=snapshot_age,
        )

    if candidate_order.cycle_id != cycle_context.cycle_id:
        return _result(
            decision=AdmissionDecision.INVALID_CANDIDATE,
            reason_code=AdmissionReasonCode.CYCLE_ID_MISMATCH,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            snapshot_age_seconds=snapshot_age,
            validation_errors=("candidate cycle id mismatch",),
        )

    candidate_error = _validate_candidate(candidate_order, policy)
    if candidate_error is not None:
        reason_code, message = candidate_error
        return _result(
            decision=AdmissionDecision.INVALID_CANDIDATE,
            reason_code=reason_code,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            snapshot_age_seconds=snapshot_age,
            validation_errors=(message,),
        )

    if candidate_order.margin_mode is not policy.supported_margin_mode:
        return _result(
            decision=AdmissionDecision.UNSUPPORTED_MARGIN_MODE,
            reason_code=AdmissionReasonCode.MARGIN_MODE_NOT_SUPPORTED,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            snapshot_age_seconds=snapshot_age,
        )

    usable_capacity = (
        account_snapshot.withdrawable
        - policy.absolute_reserve
        - policy.safety_buffer
        - cycle_context.reserved_capacity
    )
    candidate_requirement = candidate_order.requested_notional
    remaining_capacity = usable_capacity - candidate_requirement

    if candidate_requirement <= usable_capacity:
        return _result(
            decision=AdmissionDecision.ADMITTED,
            reason_code=AdmissionReasonCode.CAPACITY_SUFFICIENT,
            account_snapshot=account_snapshot,
            candidate_order=candidate_order,
            cycle_context=cycle_context,
            policy=policy,
            snapshot_age_seconds=snapshot_age,
            usable_capacity=usable_capacity,
            candidate_requirement=candidate_requirement,
            reservation_amount=candidate_requirement,
            remaining_capacity=remaining_capacity,
        )

    return _result(
        decision=AdmissionDecision.INSUFFICIENT_MARGIN,
        reason_code=AdmissionReasonCode.CAPACITY_BELOW_REQUIREMENT,
        account_snapshot=account_snapshot,
        candidate_order=candidate_order,
        cycle_context=cycle_context,
        policy=policy,
        snapshot_age_seconds=snapshot_age,
        usable_capacity=usable_capacity,
        candidate_requirement=candidate_requirement,
        remaining_capacity=remaining_capacity,
    )


def _validate_policy(policy: AdmissionPolicyV1) -> tuple[str, ...]:
    errors = []
    if policy.schema_version != "1.0":
        errors.append("unsupported policy schema version")
    for name, value in (
        ("max_snapshot_age_seconds", policy.max_snapshot_age_seconds),
        ("absolute_reserve", policy.absolute_reserve),
        ("safety_buffer", policy.safety_buffer),
        ("notional_tolerance", policy.notional_tolerance),
    ):
        if not _is_non_negative_decimal(value):
            errors.append(f"{name} must be a non-negative Decimal")
    if not isinstance(policy.supported_margin_mode, MarginMode):
        errors.append("supported margin mode is invalid")
    return tuple(errors)


def _validate_cycle_context(
    cycle_context: CycleContextV1,
) -> tuple[str, ...]:
    errors = []
    if cycle_context.schema_version != "1.0":
        errors.append("unsupported cycle context schema version")
    if not cycle_context.cycle_id:
        errors.append("cycle id is missing")
    if not cycle_context.account_snapshot_id:
        errors.append("account snapshot id is missing")
    if not _is_non_negative_decimal(cycle_context.reserved_capacity):
        errors.append("reserved capacity must be a non-negative Decimal")
    if (
        not isinstance(cycle_context.account_refresh_sequence, int)
        or isinstance(cycle_context.account_refresh_sequence, bool)
        or cycle_context.account_refresh_sequence < 0
    ):
        errors.append("account refresh sequence is invalid")
    if (
        not isinstance(cycle_context.evaluated_candidates, int)
        or isinstance(cycle_context.evaluated_candidates, bool)
        or cycle_context.evaluated_candidates < 0
    ):
        errors.append("evaluated candidates is invalid")
    if not _is_aware_datetime(cycle_context.created_at):
        errors.append("cycle created_at is invalid")
    if not _is_aware_datetime(cycle_context.updated_at):
        errors.append("cycle updated_at is invalid")
    return tuple(errors)


def _validate_account_snapshot(
    snapshot: AccountSnapshotV1,
) -> tuple[str, ...]:
    errors = []
    if snapshot.schema_version != "1.0":
        errors.append("unsupported account snapshot schema version")
    if snapshot.normalization_status is not AccountNormalizationStatus.VALID:
        errors.extend(snapshot.normalization_errors)
        if not snapshot.normalization_errors:
            errors.append("account snapshot normalization failed")
    if not snapshot.snapshot_id:
        errors.append("snapshot id is missing")
    if not snapshot.account_address:
        errors.append("account address is missing")
    if not isinstance(snapshot.environment, AccountEnvironment):
        errors.append("account environment is invalid")
    if not isinstance(snapshot.source, AccountSource):
        errors.append("account source is invalid")
    if not _is_aware_datetime(snapshot.exchange_timestamp):
        errors.append("exchange timestamp is invalid")
    if not _is_aware_datetime(snapshot.received_at):
        errors.append("received_at is invalid")
    if (
        _is_aware_datetime(snapshot.exchange_timestamp)
        and _is_aware_datetime(snapshot.received_at)
        and snapshot.received_at < snapshot.exchange_timestamp
    ):
        errors.append("received_at precedes exchange timestamp")
    for name, value in (
        ("account_value", snapshot.account_value),
        ("total_margin_used", snapshot.total_margin_used),
        ("withdrawable", snapshot.withdrawable),
    ):
        if not _is_non_negative_decimal(value):
            errors.append(f"{name} must be a non-negative Decimal")
    return tuple(errors)


def _validate_candidate(
    candidate: CandidateOrderV1,
    policy: AdmissionPolicyV1,
) -> tuple[AdmissionReasonCode, str] | None:
    if candidate.schema_version != "1.0":
        return (
            AdmissionReasonCode.INVALID_NOTIONAL,
            "unsupported candidate schema version",
        )
    if not _is_positive_decimal(candidate.requested_size):
        return AdmissionReasonCode.INVALID_SIZE, "requested size is invalid"
    if not _is_positive_decimal(candidate.reference_price):
        return AdmissionReasonCode.INVALID_PRICE, "reference price is invalid"
    if not _is_positive_decimal(candidate.requested_notional):
        return (
            AdmissionReasonCode.INVALID_NOTIONAL,
            "requested notional is invalid",
        )
    if candidate.size_normalization_status is not CandidateSizeStatus.NORMALIZED:
        return (
            AdmissionReasonCode.SIZE_NOT_NORMALIZED,
            "candidate size is not normalized",
        )
    if candidate.direction not in {"LONG", "SHORT"}:
        return AdmissionReasonCode.INVALID_DIRECTION, "direction is invalid"
    if candidate.reduce_only is not False:
        return (
            AdmissionReasonCode.REDUCE_ONLY_NOT_SUPPORTED,
            "reduce-only candidate is not supported",
        )
    if not _is_aware_datetime(candidate.created_at):
        return (
            AdmissionReasonCode.INVALID_NOTIONAL,
            "candidate created_at is invalid",
        )
    if not _is_aware_datetime(candidate.reference_price_timestamp):
        return (
            AdmissionReasonCode.INVALID_PRICE,
            "reference price timestamp is invalid",
        )
    calculated_notional = candidate.requested_size * candidate.reference_price
    if abs(calculated_notional - candidate.requested_notional) > policy.notional_tolerance:
        return (
            AdmissionReasonCode.NOTIONAL_MISMATCH,
            "requested notional does not match size and price",
        )
    return None


def _result(
    decision: AdmissionDecision,
    reason_code: AdmissionReasonCode,
    account_snapshot: AccountSnapshotV1 | None,
    candidate_order: CandidateOrderV1,
    cycle_context: CycleContextV1,
    policy: AdmissionPolicyV1,
    snapshot_age_seconds: Decimal | None = None,
    usable_capacity: Decimal | None = None,
    candidate_requirement: Decimal | None = None,
    reservation_amount: Decimal = Decimal("0"),
    remaining_capacity: Decimal | None = None,
    validation_errors: tuple[str, ...] = (),
) -> AdmissionResultV1:
    return AdmissionResultV1(
        schema_version="1.0",
        decision=decision,
        reason_code=reason_code,
        candidate_id=getattr(candidate_order, "candidate_id", None),
        cycle_id=getattr(cycle_context, "cycle_id", None),
        snapshot_id=(
            account_snapshot.snapshot_id
            if account_snapshot is not None
            else getattr(cycle_context, "account_snapshot_id", None)
        ),
        account_refresh_sequence=getattr(
            cycle_context,
            "account_refresh_sequence",
            None,
        ),
        evaluated_at=getattr(cycle_context, "updated_at", None),
        snapshot_age_seconds=snapshot_age_seconds,
        account_value=(
            account_snapshot.account_value
            if account_snapshot is not None
            and _is_finite_decimal(account_snapshot.account_value)
            else None
        ),
        total_margin_used=(
            account_snapshot.total_margin_used
            if account_snapshot is not None
            and _is_finite_decimal(account_snapshot.total_margin_used)
            else None
        ),
        withdrawable=(
            account_snapshot.withdrawable
            if account_snapshot is not None
            and _is_finite_decimal(account_snapshot.withdrawable)
            else None
        ),
        reserved_capacity=(
            cycle_context.reserved_capacity
            if _is_finite_decimal(cycle_context.reserved_capacity)
            else Decimal("0")
        ),
        absolute_reserve=(
            policy.absolute_reserve
            if _is_finite_decimal(policy.absolute_reserve)
            else Decimal("0")
        ),
        safety_buffer=(
            policy.safety_buffer
            if _is_finite_decimal(policy.safety_buffer)
            else Decimal("0")
        ),
        usable_capacity=usable_capacity,
        requested_size=(
            candidate_order.requested_size
            if _is_finite_decimal(candidate_order.requested_size)
            else None
        ),
        reference_price=(
            candidate_order.reference_price
            if _is_finite_decimal(candidate_order.reference_price)
            else None
        ),
        candidate_notional=(
            candidate_order.requested_notional
            if _is_finite_decimal(candidate_order.requested_notional)
            else None
        ),
        candidate_requirement=candidate_requirement,
        reservation_amount=reservation_amount,
        remaining_capacity=remaining_capacity,
        validation_errors=validation_errors,
    )


def _is_finite_decimal(value: object) -> bool:
    return isinstance(value, Decimal) and value.is_finite()


def _is_non_negative_decimal(value: object) -> bool:
    return _is_finite_decimal(value) and value >= 0


def _is_positive_decimal(value: object) -> bool:
    return _is_finite_decimal(value) and value > 0


def _is_aware_datetime(value: object) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    return Decimal(str((later - earlier).total_seconds()))
