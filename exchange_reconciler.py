"""
Exchange Reconciler

Responsabilidad:

- Comparar las posiciones OPEN de SQLite con las posiciones reales
  existentes en Hyperliquid.
- Detectar posiciones que ya no existen en el exchange.
- Confirmar su cierre mediante fills reales de Hyperliquid.
- Obtener el PnL realizado directamente del exchange.
- Delegar el cambio de estado local a positions.close_position().

Este módulo no abre posiciones ni ejecuta órdenes.
"""


import json
import sqlite3
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum

from account_snapshot import get_account_snapshot
from hyperliquid_client import get_info
from hyperliquid_poc.config import ACCOUNT_ADDRESS
from margin_admission import AccountNormalizationStatus
from positions import close_position


RECONCILIATION_SCHEMA_VERSION = "1.0"
RECONCILIATION_TTL_SECONDS = 10
DEFAULT_MAX_SNAPSHOT_AGE_SECONDS = 10
DEFAULT_SIZE_TOLERANCE = Decimal("0")


class ReconciliationState(Enum):
    CONFIRMED = "CONFIRMED"
    SIZE_MISMATCH = "SIZE_MISMATCH"
    EXCHANGE_ONLY = "EXCHANGE_ONLY"
    LOCAL_ONLY = "LOCAL_ONLY"
    UNKNOWN = "UNKNOWN"
    STALE_DATA = "STALE_DATA"


class ReconciliationCapability(Enum):
    OPEN_AND_REDUCE = "OPEN_AND_REDUCE"
    REDUCE_ONLY = "REDUCE_ONLY"
    NO_AUTOMATED_EXECUTION = "NO_AUTOMATED_EXECUTION"


@dataclass(frozen=True)
class ReconciliationResult:
    schema_version: str
    reconciliation_id: str
    cycle_id: str
    state: ReconciliationState
    capability: ReconciliationCapability
    snapshot_id: str | None
    snapshot_timestamp: datetime | None
    evaluated_at: datetime
    valid_until: datetime
    blocking_reason: str | None
    details: dict
    is_final: bool


@dataclass(frozen=True)
class LocalExposure:
    asset: str
    signed_size: Decimal
    entry_price: Decimal | None
    position_ids: tuple[str, ...]


@dataclass(frozen=True)
class ActiveOrder:
    oid: int
    asset: str
    side: str
    size: Decimal | None
    original_size: Decimal | None
    trigger_price: Decimal | None
    is_trigger: object
    reduce_only: object


_FRONTEND_ORDERS_UNSET = object()


def _normalize_order_id(order_id):
    """
    Convierte un identificador de orden a entero.

    Devuelve None cuando el identificador está ausente
    o no puede convertirse.
    """
    if order_id is None:
        return None

    try:
        return int(order_id)
    except (TypeError, ValueError):
        return None

def _is_close_fill(fill, asset):
    """
    Determina si un fill corresponde al cierre total o parcial
    de una posición del activo indicado.
    """
    if fill.get("coin") != asset:
        return False

    direction = str(fill.get("dir", "")).strip()

    return (
        direction.startswith("Close ")
        or " > " in direction
    )


def _find_close_fill(
    fills,
    asset,
    opened_at,
    stop_loss_order_id,
    take_profit_order_id,
):
    """
    Busca el fill de cierre más reciente de un activo.

    Prioridad de clasificación:

    1. STOP_LOSS:
       El OID del fill coincide con stop_loss_order_id.

    2. TAKE_PROFIT:
       El OID del fill coincide con take_profit_order_id.

    3. EXCHANGE_CLOSE:
       Existe un fill real de cierre, pero no coincide con las
       órdenes protectoras conocidas. Puede ser un cierre manual,
       externo o una orden cuyo ID no fue persistido correctamente.

    Devuelve:

        (fill, motivo)

    o:

        (None, "UNKNOWN")
    """
    normalized_stop_loss_id = _normalize_order_id(
        stop_loss_order_id
    )
    normalized_take_profit_id = _normalize_order_id(
        take_profit_order_id
    )

    try:
        opened_at_dt = datetime.fromisoformat(str(opened_at))
        if opened_at_dt.tzinfo is None:
            opened_at_dt = opened_at_dt.replace(
                tzinfo=timezone.utc
            )
        opened_at_ms = int(opened_at_dt.timestamp() * 1000)
    except (TypeError, ValueError):
        return None, "INVALID_OPENED_AT"

    close_fills = [
        fill
        for fill in fills
        if (
            _is_close_fill(fill, asset)
            and int(fill.get("time", 0)) >= opened_at_ms
        )
    ]

    if not close_fills:
        return None, "UNKNOWN"

    close_fills.sort(
        key=lambda fill: int(fill.get("time", 0)),
        reverse=True,
    )

    for fill in close_fills:
        fill_order_id = _normalize_order_id(
            fill.get("oid")
        )

        if (
            normalized_stop_loss_id is not None
            and fill_order_id == normalized_stop_loss_id
        ):
            return fill, "STOP_LOSS"

        if (
            normalized_take_profit_id is not None
            and fill_order_id == normalized_take_profit_id
        ):
            return fill, "TAKE_PROFIT"

    return close_fills[0], "EXCHANGE_CLOSE"


def _ensure_reconciliation_results_table(
    conn: sqlite3.Connection,
) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reconciliation_results (
            reconciliation_id TEXT PRIMARY KEY,
            cycle_id TEXT NOT NULL,
            state TEXT NOT NULL,
            capability TEXT NOT NULL,
            snapshot_id TEXT,
            snapshot_timestamp TEXT,
            evaluated_at TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            blocking_reason TEXT,
            details_json TEXT NOT NULL,
            is_final INTEGER NOT NULL
                CHECK (is_final IN (0, 1)),
            CHECK (
                state IN (
                    'CONFIRMED',
                    'SIZE_MISMATCH',
                    'EXCHANGE_ONLY',
                    'LOCAL_ONLY',
                    'UNKNOWN',
                    'STALE_DATA'
                )
            ),
            CHECK (
                capability IN (
                    'OPEN_AND_REDUCE',
                    'REDUCE_ONLY',
                    'NO_AUTOMATED_EXECUTION'
                )
            )
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_reconciliation_cycle_evaluated
        ON reconciliation_results (
            cycle_id,
            evaluated_at DESC
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_reconciliation_valid_until
        ON reconciliation_results (
            valid_until
        )
        """
    )


def _decimal(value) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None

    if not decimal_value.is_finite():
        return None

    return decimal_value


def _load_cycle_id(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        """
        SELECT value
        FROM system_state
        WHERE key = 'current_cycle_id'
        """
    ).fetchone()

    if row is None or not str(row[0]).strip():
        raise ValueError("current_cycle_id is missing")

    return str(row[0])


def _load_open_position_rows(conn: sqlite3.Connection):
    return conn.execute(
        """
        SELECT
            position_id,
            asset,
            direction,
            entry_price,
            current_price,
            position_size,
            opened_at,
            exchange_order_id,
            stop_loss_order_id,
            take_profit_order_id
        FROM positions
        WHERE status = 'OPEN'
        """
    ).fetchall()


def _local_direction_ambiguities(sqlite_positions):
    directions_by_asset = {}

    for row in sqlite_positions:
        asset = row[1]
        direction = str(row[2]).upper()
        directions_by_asset.setdefault(asset, set()).add(direction)

    return [
        {
            "asset": asset,
            "directions": sorted(directions),
        }
        for asset, directions in sorted(directions_by_asset.items())
        if "LONG" in directions and "SHORT" in directions
    ]


def _normalize_frontend_open_orders(raw_orders):
    if not isinstance(raw_orders, list):
        raise ValueError("PROTECTION_RESPONSE_INVALID")

    orders = {}

    for raw_order in raw_orders:
        if not isinstance(raw_order, dict):
            raise ValueError("PROTECTION_RESPONSE_INVALID")

        oid = _normalize_order_id(raw_order.get("oid"))
        if oid is None:
            raise ValueError("PROTECTION_RESPONSE_INVALID")
        if oid in orders:
            raise ValueError("PROTECTION_OID_AMBIGUOUS")

        asset = raw_order.get("coin")
        side = raw_order.get("side")
        if not isinstance(asset, str) or not asset:
            raise ValueError("PROTECTION_RESPONSE_INVALID")
        if not isinstance(side, str) or not side:
            raise ValueError("PROTECTION_RESPONSE_INVALID")

        orders[oid] = ActiveOrder(
            oid=oid,
            asset=asset,
            side=side,
            size=_decimal(raw_order.get("sz")),
            original_size=_decimal(raw_order.get("origSz")),
            trigger_price=_decimal(raw_order.get("triggerPx")),
            is_trigger=raw_order.get("isTrigger"),
            reduce_only=raw_order.get("reduceOnly"),
        )

    return orders


def _protection_evidence(expected_oid):
    return {
        "expected_oid": (
            str(expected_oid) if expected_oid is not None else None
        ),
        "observed": False,
        "valid": False,
        "observed_asset": None,
        "observed_side": None,
        "observed_size": None,
        "observed_orig_size": None,
        "observed_trigger_price": None,
        "observed_is_trigger": None,
        "observed_reduce_only": None,
        "failure_reason": None,
    }


def _validate_expected_protection(
    *,
    expected_oid,
    missing_id_reason,
    protection_kind,
    asset,
    direction,
    required_size,
    exchange_entry_price,
    active_orders,
    size_tolerance,
    ambiguous_expected_oids,
):
    evidence = _protection_evidence(expected_oid)
    normalized_oid = _normalize_order_id(expected_oid)

    if normalized_oid is None:
        evidence["failure_reason"] = missing_id_reason
        return evidence
    if normalized_oid in ambiguous_expected_oids:
        evidence["failure_reason"] = "PROTECTION_OID_AMBIGUOUS"
        return evidence

    order = active_orders.get(normalized_oid)
    if order is None:
        evidence["failure_reason"] = "PROTECTION_MISSING"
        return evidence

    evidence.update(
        {
            "observed": True,
            "observed_asset": order.asset,
            "observed_side": order.side,
            "observed_size": (
                str(order.size) if order.size is not None else None
            ),
            "observed_orig_size": (
                str(order.original_size)
                if order.original_size is not None
                else None
            ),
            "observed_trigger_price": (
                str(order.trigger_price)
                if order.trigger_price is not None
                else None
            ),
            "observed_is_trigger": order.is_trigger,
            "observed_reduce_only": order.reduce_only,
        }
    )

    if order.asset != asset:
        evidence["failure_reason"] = "PROTECTION_ASSET_MISMATCH"
    elif order.is_trigger is not True:
        evidence["failure_reason"] = "PROTECTION_NOT_TRIGGER"
    elif order.reduce_only is not True:
        evidence["failure_reason"] = "PROTECTION_NOT_REDUCE_ONLY"
    else:
        expected_side = "A" if direction == "LONG" else "B"
        if order.side != expected_side:
            evidence["failure_reason"] = "PROTECTION_SIDE_INVALID"
        elif order.size is None or order.size <= 0:
            evidence["failure_reason"] = "PROTECTION_SIZE_INSUFFICIENT"
        elif order.size + size_tolerance < required_size:
            evidence["failure_reason"] = "PROTECTION_SIZE_INSUFFICIENT"
        elif order.trigger_price is None or order.trigger_price <= 0:
            evidence["failure_reason"] = "PROTECTION_TRIGGER_INVALID"
        elif exchange_entry_price is None or exchange_entry_price <= 0:
            evidence["failure_reason"] = "PROTECTION_SEMANTICS_INVALID"
        else:
            if direction == "LONG":
                semantics_valid = (
                    order.trigger_price < exchange_entry_price
                    if protection_kind == "stop_loss"
                    else order.trigger_price > exchange_entry_price
                )
            else:
                semantics_valid = (
                    order.trigger_price > exchange_entry_price
                    if protection_kind == "stop_loss"
                    else order.trigger_price < exchange_entry_price
                )

            if not semantics_valid:
                evidence["failure_reason"] = "PROTECTION_SEMANTICS_INVALID"

    evidence["valid"] = evidence["failure_reason"] is None
    return evidence


def _validate_protections(
    *,
    sqlite_positions,
    exchange_exposures,
    raw_frontend_orders,
    size_tolerance,
):
    try:
        active_orders = _normalize_frontend_open_orders(raw_frontend_orders)
    except ValueError as exc:
        reason = str(exc)
        return False, reason, {
            "required": True,
            "status": "UNKNOWN",
            "expected_count": len(sqlite_positions) * 2,
            "observed_active_order_count": (
                len(raw_frontend_orders)
                if isinstance(raw_frontend_orders, list)
                else None
            ),
            "positions": [],
            "errors": [reason],
        }

    expected_oid_counts = {}
    for row in sqlite_positions:
        for expected_oid in (row[8], row[9]):
            normalized_oid = _normalize_order_id(expected_oid)
            if normalized_oid is not None:
                expected_oid_counts[normalized_oid] = (
                    expected_oid_counts.get(normalized_oid, 0) + 1
                )
    ambiguous_expected_oids = {
        oid for oid, count in expected_oid_counts.items() if count > 1
    }

    position_evidence = []
    errors = []
    coverage = {}

    for row in sqlite_positions:
        (
            position_id,
            asset,
            direction,
            _entry_price,
            _current_price,
            position_size,
            _opened_at,
            _exchange_order_id,
            stop_loss_order_id,
            take_profit_order_id,
        ) = row
        normalized_direction = str(direction).upper()
        required_size = _decimal(position_size)
        exchange_position = exchange_exposures.get(asset)
        exchange_entry_price = (
            exchange_position.entry_price
            if exchange_position is not None
            else None
        )

        if (
            normalized_direction not in {"LONG", "SHORT"}
            or required_size is None
            or required_size <= 0
        ):
            raise ValueError(f"invalid local position for {position_id}")

        sl_evidence = _validate_expected_protection(
            expected_oid=stop_loss_order_id,
            missing_id_reason="STOP_LOSS_ID_MISSING",
            protection_kind="stop_loss",
            asset=asset,
            direction=normalized_direction,
            required_size=required_size,
            exchange_entry_price=exchange_entry_price,
            active_orders=active_orders,
            size_tolerance=size_tolerance,
            ambiguous_expected_oids=ambiguous_expected_oids,
        )
        tp_evidence = _validate_expected_protection(
            expected_oid=take_profit_order_id,
            missing_id_reason="TAKE_PROFIT_ID_MISSING",
            protection_kind="take_profit",
            asset=asset,
            direction=normalized_direction,
            required_size=required_size,
            exchange_entry_price=exchange_entry_price,
            active_orders=active_orders,
            size_tolerance=size_tolerance,
            ambiguous_expected_oids=ambiguous_expected_oids,
        )

        for item in (sl_evidence, tp_evidence):
            if item["failure_reason"] is not None:
                errors.append(item["failure_reason"])

        asset_coverage = coverage.setdefault(
            asset,
            {"stop_loss": Decimal("0"), "take_profit": Decimal("0")},
        )
        if sl_evidence["valid"]:
            asset_coverage["stop_loss"] += active_orders[
                _normalize_order_id(stop_loss_order_id)
            ].size
        if tp_evidence["valid"]:
            asset_coverage["take_profit"] += active_orders[
                _normalize_order_id(take_profit_order_id)
            ].size

        position_evidence.append(
            {
                "position_id": str(position_id),
                "asset": asset,
                "direction": normalized_direction,
                "required_size": str(required_size),
                "stop_loss": sl_evidence,
                "take_profit": tp_evidence,
            }
        )

    for asset, exchange_position in exchange_exposures.items():
        if asset not in coverage:
            continue
        required_exchange_size = abs(exchange_position.signed_size)
        for protection_kind in ("stop_loss", "take_profit"):
            if (
                coverage[asset][protection_kind] + size_tolerance
                < required_exchange_size
            ):
                errors.append("PROTECTION_SIZE_INSUFFICIENT")

    unique_errors = list(dict.fromkeys(errors))
    valid = not unique_errors
    details = {
        "required": True,
        "status": "CONFIRMED" if valid else "FAILED",
        "expected_count": len(sqlite_positions) * 2,
        "observed_active_order_count": len(active_orders),
        "positions": position_evidence,
        "errors": unique_errors,
    }
    return (
        valid,
        None if valid else unique_errors[0],
        details,
    )


def _exchange_direction(signed_size: Decimal) -> str:
    if signed_size > 0:
        return "LONG"
    if signed_size < 0:
        return "SHORT"
    raise ValueError("zero size does not have a direction")


def _exchange_position_pairs(account_snapshot):
    return {
        (
            position.asset,
            _exchange_direction(position.signed_size),
        )
        for position in account_snapshot.asset_positions
        if position.signed_size != 0
    }


def _resolve_existing_local_closures(
    conn: sqlite3.Connection,
    *,
    sqlite_positions,
    exchange_positions_set,
    fills,
):
    """Preserva la politica existente de cierre por fills."""
    automatic_actions = []
    unresolved_positions = []

    for row in sqlite_positions:
        (
            position_id,
            asset,
            direction,
            entry_price,
            current_price,
            position_size,
            opened_at,
            exchange_order_id,
            stop_loss_order_id,
            take_profit_order_id,
        ) = row

        if (asset, direction) in exchange_positions_set:
            continue

        difference = {
            "position_id": position_id,
            "asset": asset,
            "direction": direction,
            "position_size": position_size,
            "opened_at": opened_at,
            "realized_pnl": None,
            "reconcile_status": "UNKNOWN",
        }

        is_legacy_position = (
            exchange_order_id is None
            and float(entry_price or 0) == 0
        )

        if is_legacy_position:
            difference["reconcile_status"] = "LEGACY"
            difference["realized_pnl"] = 0.0
        else:
            close_fill, close_reason = _find_close_fill(
                fills=fills,
                asset=asset,
                opened_at=opened_at,
                stop_loss_order_id=stop_loss_order_id,
                take_profit_order_id=take_profit_order_id,
            )
            difference["reconcile_status"] = close_reason

            if close_fill is not None:
                try:
                    difference["realized_pnl"] = float(
                        close_fill.get("closedPnl", 0)
                    )
                except (TypeError, ValueError):
                    difference["realized_pnl"] = None
                    difference["reconcile_status"] = (
                        "INVALID_CLOSED_PNL"
                    )

                difference["close_price"] = close_fill.get("px")
                difference["close_order_id"] = close_fill.get("oid")
                difference["close_time"] = close_fill.get("time")

        print(
            f"{difference['asset']:10} "
            f"{difference['reconcile_status']:20} "
            f"{difference['direction']:8} "
            f"size={difference['position_size']} "
            f"pnl={difference['realized_pnl']}"
        )

        if difference["realized_pnl"] is None:
            unresolved_positions.append(difference)
            print(
                "[RECONCILER] Position remains OPEN: "
                f"{asset} has no verified exchange close fill."
            )
            continue

        close_position(
            conn,
            difference["position_id"],
            difference["realized_pnl"],
        )
        automatic_actions.append(
            {
                "action": "LOCAL_POSITION_CLOSED",
                **difference,
            }
        )
        print(
            f"[RECONCILER] Closed {asset} "
            f"reason={difference['reconcile_status']} "
            f"realized_pnl={difference['realized_pnl']}"
        )

    return automatic_actions, unresolved_positions


def _load_local_exposures(conn: sqlite3.Connection):
    rows = conn.execute(
        """
        SELECT
            position_id,
            asset,
            direction,
            position_size,
            entry_price
        FROM positions
        WHERE status = 'OPEN'
        """
    ).fetchall()
    grouped = {}

    for position_id, asset, direction, position_size, entry_price in rows:
        if not isinstance(asset, str) or not asset:
            raise ValueError(f"invalid local asset for {position_id}")

        size = _decimal(position_size)
        if size is None or size <= 0:
            raise ValueError(f"invalid local size for {position_id}")

        normalized_direction = str(direction).upper()
        if normalized_direction == "LONG":
            signed_size = size
        elif normalized_direction == "SHORT":
            signed_size = -size
        else:
            raise ValueError(
                f"invalid local direction for {position_id}"
            )

        values = grouped.setdefault(
            asset,
            {
                "signed_size": Decimal("0"),
                "weighted_entry_total": Decimal("0"),
                "entry_weight": Decimal("0"),
                "position_ids": [],
            },
        )
        values["signed_size"] += signed_size
        values["position_ids"].append(str(position_id))

        normalized_entry = _decimal(entry_price)
        if normalized_entry is not None and normalized_entry > 0:
            values["weighted_entry_total"] += normalized_entry * size
            values["entry_weight"] += size

    exposures = {}
    for asset, values in grouped.items():
        entry_price = None
        if values["entry_weight"] > 0:
            entry_price = (
                values["weighted_entry_total"]
                / values["entry_weight"]
            )

        exposures[asset] = LocalExposure(
            asset=asset,
            signed_size=values["signed_size"],
            entry_price=entry_price,
            position_ids=tuple(values["position_ids"]),
        )

    return exposures


def _load_exchange_exposures(account_snapshot):
    exposures = {}
    for position in account_snapshot.asset_positions:
        if position.signed_size == 0:
            continue
        if position.asset in exposures:
            raise ValueError(
                f"duplicate exchange asset: {position.asset}"
            )
        exposures[position.asset] = position
    return exposures


def _classify_final_state(
    *,
    local_exposures,
    exchange_exposures,
    size_tolerance,
    automatic_actions,
    unresolved_positions,
):
    assets = sorted(set(local_exposures) | set(exchange_exposures))
    comparisons = []
    states = []

    for asset in assets:
        local = local_exposures.get(asset)
        exchange = exchange_exposures.get(asset)
        local_size = (
            local.signed_size if local is not None else Decimal("0")
        )
        exchange_size = (
            exchange.signed_size
            if exchange is not None
            else Decimal("0")
        )
        size_delta = abs(local_size - exchange_size)

        if local is None:
            state = ReconciliationState.EXCHANGE_ONLY
        elif exchange is None:
            state = ReconciliationState.LOCAL_ONLY
        elif size_delta > size_tolerance:
            state = ReconciliationState.SIZE_MISMATCH
        else:
            state = ReconciliationState.CONFIRMED

        states.append(state)
        comparisons.append(
            {
                "asset": asset,
                "state": state.value,
                "local_signed_size": str(local_size),
                "exchange_signed_size": str(exchange_size),
                "size_delta": str(size_delta),
                "direction_mismatch": (
                    local_size != 0
                    and exchange_size != 0
                    and (local_size > 0) != (exchange_size > 0)
                ),
                "local_entry_price": (
                    str(local.entry_price)
                    if local is not None and local.entry_price is not None
                    else None
                ),
                "exchange_entry_price": (
                    str(exchange.entry_price)
                    if (
                        exchange is not None
                        and exchange.entry_price is not None
                    )
                    else None
                ),
                "position_ids": (
                    list(local.position_ids) if local is not None else []
                ),
            }
        )

    details = {
        "assets": comparisons,
        "automatic_actions": automatic_actions,
        "unresolved_positions": unresolved_positions,
        "size_tolerance": str(size_tolerance),
    }

    if not states or all(
        state == ReconciliationState.CONFIRMED for state in states
    ):
        return (
            ReconciliationState.CONFIRMED,
            ReconciliationCapability.OPEN_AND_REDUCE,
            None,
            details,
        )

    priority = (
        ReconciliationState.EXCHANGE_ONLY,
        ReconciliationState.SIZE_MISMATCH,
        ReconciliationState.LOCAL_ONLY,
    )
    global_state = next(
        state for state in priority if state in states
    )
    return (
        global_state,
        ReconciliationCapability.REDUCE_ONLY,
        global_state.value,
        details,
    )


def _persist_reconciliation_result(
    conn: sqlite3.Connection,
    result: ReconciliationResult,
) -> None:
    conn.execute(
        """
        INSERT INTO reconciliation_results (
            reconciliation_id,
            cycle_id,
            state,
            capability,
            snapshot_id,
            snapshot_timestamp,
            evaluated_at,
            valid_until,
            blocking_reason,
            details_json,
            is_final
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result.reconciliation_id,
            result.cycle_id,
            result.state.value,
            result.capability.value,
            result.snapshot_id,
            (
                result.snapshot_timestamp.isoformat()
                if result.snapshot_timestamp is not None
                else None
            ),
            result.evaluated_at.isoformat(),
            result.valid_until.isoformat(),
            result.blocking_reason,
            json.dumps(result.details, sort_keys=True, separators=(",", ":")),
            1 if result.is_final else 0,
        ),
    )


def _unknown_result(
    *,
    cycle_id,
    evaluated_at,
    blocking_reason,
    errors,
    snapshot_id=None,
    snapshot_timestamp=None,
):
    return ReconciliationResult(
        schema_version=RECONCILIATION_SCHEMA_VERSION,
        reconciliation_id=str(uuid.uuid4()),
        cycle_id=cycle_id,
        state=ReconciliationState.UNKNOWN,
        capability=ReconciliationCapability.NO_AUTOMATED_EXECUTION,
        snapshot_id=snapshot_id,
        snapshot_timestamp=snapshot_timestamp,
        evaluated_at=evaluated_at,
        valid_until=evaluated_at,
        blocking_reason=blocking_reason,
        details={"errors": errors},
        is_final=True,
    )


def _stale_result(
    *,
    cycle_id,
    evaluated_at,
    account_snapshot,
    snapshot_age_seconds,
    max_snapshot_age_seconds,
):
    return ReconciliationResult(
        schema_version=RECONCILIATION_SCHEMA_VERSION,
        reconciliation_id=str(uuid.uuid4()),
        cycle_id=cycle_id,
        state=ReconciliationState.STALE_DATA,
        capability=ReconciliationCapability.NO_AUTOMATED_EXECUTION,
        snapshot_id=account_snapshot.snapshot_id,
        snapshot_timestamp=account_snapshot.exchange_timestamp,
        evaluated_at=evaluated_at,
        valid_until=evaluated_at,
        blocking_reason="SNAPSHOT_STALE",
        details={
            "snapshot_age_seconds": snapshot_age_seconds,
            "max_snapshot_age_seconds": max_snapshot_age_seconds,
        },
        is_final=True,
    )


def _evaluation_time(evaluated_at=None) -> datetime:
    if evaluated_at is not None:
        return evaluated_at.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def reconcile(
    conn: sqlite3.Connection,
    *,
    account_snapshot=None,
    fills=None,
    frontend_orders=_FRONTEND_ORDERS_UNSET,
    evaluated_at=None,
    max_snapshot_age_seconds=DEFAULT_MAX_SNAPSHOT_AGE_SECONDS,
    size_tolerance=DEFAULT_SIZE_TOLERANCE,
) -> ReconciliationResult:
    """Reconcilia, clasifica y persiste evidencia del estado final."""
    _ensure_reconciliation_results_table(conn)

    try:
        cycle_id = _load_cycle_id(conn)
    except Exception as exc:
        cycle_id = "UNKNOWN"
        decision_at = _evaluation_time(evaluated_at)
        result = _unknown_result(
            cycle_id=cycle_id,
            evaluated_at=decision_at,
            blocking_reason="CYCLE_ID_UNAVAILABLE",
            errors=[f"{type(exc).__name__}: {exc}"],
        )
        _persist_reconciliation_result(conn, result)
        conn.commit()
        return result

    try:
        snapshot = (
            account_snapshot
            if account_snapshot is not None
            else get_account_snapshot()
        )
        snapshot_check_at = _evaluation_time(evaluated_at)

        if (
            snapshot.normalization_status
            != AccountNormalizationStatus.VALID
        ):
            result = _unknown_result(
                cycle_id=cycle_id,
                evaluated_at=snapshot_check_at,
                blocking_reason="SNAPSHOT_INVALID",
                errors=list(snapshot.normalization_errors),
                snapshot_id=snapshot.snapshot_id,
                snapshot_timestamp=snapshot.exchange_timestamp,
            )
            _persist_reconciliation_result(conn, result)
            conn.commit()
            return result

        snapshot_age_seconds = (
            snapshot_check_at - snapshot.exchange_timestamp
        ).total_seconds()
        if (
            snapshot_age_seconds < 0
            or snapshot_age_seconds > max_snapshot_age_seconds
        ):
            result = _stale_result(
                cycle_id=cycle_id,
                evaluated_at=snapshot_check_at,
                account_snapshot=snapshot,
                snapshot_age_seconds=snapshot_age_seconds,
                max_snapshot_age_seconds=max_snapshot_age_seconds,
            )
            _persist_reconciliation_result(conn, result)
            conn.commit()
            return result

        sqlite_positions = _load_open_position_rows(conn)
        exchange_positions_set = _exchange_position_pairs(snapshot)
        exchange_fills = (
            fills
            if fills is not None
            else get_info().user_fills(ACCOUNT_ADDRESS)
        )

        print(
            "[RECONCILER] SQLite OPEN positions: "
            f"{len(sqlite_positions)}"
        )
        print(
            "[RECONCILER] Exchange OPEN positions: "
            f"{len(snapshot.asset_positions)}"
        )

        automatic_actions, unresolved_positions = (
            _resolve_existing_local_closures(
                conn,
                sqlite_positions=sqlite_positions,
                exchange_positions_set=exchange_positions_set,
                fills=exchange_fills,
            )
        )

        # Preserve existing close mutations before evaluating final state.
        conn.commit()

        final_sqlite_positions = _load_open_position_rows(conn)
        local_direction_ambiguities = _local_direction_ambiguities(
            final_sqlite_positions
        )
        local_exposures = _load_local_exposures(conn)
        exchange_exposures = _load_exchange_exposures(snapshot)
        state, capability, blocking_reason, details = (
            _classify_final_state(
                local_exposures=local_exposures,
                exchange_exposures=exchange_exposures,
                size_tolerance=size_tolerance,
                automatic_actions=automatic_actions,
                unresolved_positions=unresolved_positions,
            )
        )

        if local_direction_ambiguities:
            state = ReconciliationState.UNKNOWN
            capability = ReconciliationCapability.NO_AUTOMATED_EXECUTION
            blocking_reason = "LOCAL_DIRECTION_AMBIGUOUS"
            details["local_direction_ambiguities"] = (
                local_direction_ambiguities
            )
            details["protection_validation"] = {
                "required": True,
                "status": "NOT_EVALUATED",
                "expected_count": len(final_sqlite_positions) * 2,
                "observed_active_order_count": None,
                "positions": [],
                "errors": ["LOCAL_DIRECTION_AMBIGUOUS"],
            }
        elif state == ReconciliationState.CONFIRMED:
            if final_sqlite_positions:
                try:
                    raw_frontend_orders = (
                        frontend_orders
                        if frontend_orders is not _FRONTEND_ORDERS_UNSET
                        else get_info().frontend_open_orders(ACCOUNT_ADDRESS)
                    )
                except Exception as exc:
                    protection_valid = False
                    protection_reason = "PROTECTION_OBSERVATION_ERROR"
                    protection_details = {
                        "required": True,
                        "status": "UNKNOWN",
                        "expected_count": len(final_sqlite_positions) * 2,
                        "observed_active_order_count": None,
                        "positions": [],
                        "errors": [
                            f"{protection_reason}: "
                            f"{type(exc).__name__}: {exc}"
                        ],
                    }
                else:
                    (
                        protection_valid,
                        protection_reason,
                        protection_details,
                    ) = _validate_protections(
                        sqlite_positions=final_sqlite_positions,
                        exchange_exposures=exchange_exposures,
                        raw_frontend_orders=raw_frontend_orders,
                        size_tolerance=size_tolerance,
                    )

                details["protection_validation"] = protection_details
                if not protection_valid:
                    state = ReconciliationState.UNKNOWN
                    capability = (
                        ReconciliationCapability.NO_AUTOMATED_EXECUTION
                    )
                    blocking_reason = (
                        protection_reason or "PROTECTION_UNCONFIRMED"
                    )
            else:
                details["protection_validation"] = {
                    "required": False,
                    "status": "NOT_REQUIRED",
                    "expected_count": 0,
                    "observed_active_order_count": None,
                    "positions": [],
                    "errors": [],
                }
        else:
            details["protection_validation"] = {
                "required": bool(final_sqlite_positions),
                "status": "NOT_EVALUATED",
                "expected_count": len(final_sqlite_positions) * 2,
                "observed_active_order_count": None,
                "positions": [],
                "errors": [],
            }

        decision_at = _evaluation_time(evaluated_at)
        final_snapshot_age_seconds = (
            decision_at - snapshot.exchange_timestamp
        ).total_seconds()
        if (
            final_snapshot_age_seconds < 0
            or final_snapshot_age_seconds > max_snapshot_age_seconds
        ):
            result = _stale_result(
                cycle_id=cycle_id,
                evaluated_at=decision_at,
                account_snapshot=snapshot,
                snapshot_age_seconds=final_snapshot_age_seconds,
                max_snapshot_age_seconds=max_snapshot_age_seconds,
            )
            _persist_reconciliation_result(conn, result)
            conn.commit()
            return result

        if state == ReconciliationState.UNKNOWN:
            valid_until = decision_at
        else:
            valid_until = min(
                decision_at + timedelta(
                    seconds=RECONCILIATION_TTL_SECONDS
                ),
                snapshot.exchange_timestamp + timedelta(
                    seconds=max_snapshot_age_seconds
                ),
            )

        result = ReconciliationResult(
            schema_version=RECONCILIATION_SCHEMA_VERSION,
            reconciliation_id=str(uuid.uuid4()),
            cycle_id=cycle_id,
            state=state,
            capability=capability,
            snapshot_id=snapshot.snapshot_id,
            snapshot_timestamp=snapshot.exchange_timestamp,
            evaluated_at=decision_at,
            valid_until=valid_until,
            blocking_reason=blocking_reason,
            details=details,
            is_final=True,
        )
        _persist_reconciliation_result(conn, result)
        conn.commit()
        return result

    except Exception as exc:
        conn.rollback()
        _ensure_reconciliation_results_table(conn)
        decision_at = _evaluation_time(evaluated_at)
        result = _unknown_result(
            cycle_id=cycle_id,
            evaluated_at=decision_at,
            blocking_reason="RECONCILIATION_ERROR",
            errors=[f"{type(exc).__name__}: {exc}"],
        )
        _persist_reconciliation_result(conn, result)
        conn.commit()
        return result


def main() -> None:
    conn = sqlite3.connect("trading_system.db")
    result = reconcile(conn)
    conn.close()

    print(
        "[RECONCILER] "
        f"state={result.state.value} "
        f"capability={result.capability.value} "
        f"cycle_id={result.cycle_id} "
        f"snapshot_id={result.snapshot_id} "
        f"blocking_reason={result.blocking_reason}"
    )

    if (
        result.capability
        == ReconciliationCapability.NO_AUTOMATED_EXECUTION
    ):
        sys.exit(20)


if __name__ == "__main__":
    main()
