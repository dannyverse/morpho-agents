import importlib.util
import json
import sqlite3
import sys
import types
import unittest
from unittest import mock
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from margin_admission import (
    AccountEnvironment,
    AccountNormalizationStatus,
    AccountSnapshotV1,
    AccountSource,
    MarginMode,
)


UTC = timezone.utc
NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)


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


def _test_close_position(conn, position_id, realized_pnl):
    conn.execute(
        """
        UPDATE positions
        SET
            status = 'CLOSED',
            realized_pnl = ?,
            updated_at = ?
        WHERE position_id = ?
        """,
        (
            realized_pnl,
            NOW.isoformat(),
            position_id,
        ),
    )


def _load_isolated_reconciler():
    module_path = Path(__file__).resolve().parent / "exchange_reconciler.py"
    module_name = "_test_exchange_reconciler"
    positions_stub = types.ModuleType("positions")
    positions_stub.close_position = _test_close_position
    account_snapshot_stub = types.ModuleType("account_snapshot")
    account_snapshot_stub.get_account_snapshot = lambda: None
    hyperliquid_client_stub = types.ModuleType("hyperliquid_client")

    class InfoStub:
        def user_fills(self, _address):
            return []

        def frontend_open_orders(self, _address):
            return []

    hyperliquid_client_stub.get_info = lambda: InfoStub()
    hyperliquid_poc_stub = types.ModuleType("hyperliquid_poc")
    hyperliquid_poc_stub.__path__ = []
    hyperliquid_config_stub = types.ModuleType("hyperliquid_poc.config")
    hyperliquid_config_stub.ACCOUNT_ADDRESS = "0xaccount"
    module_stubs = {
        "positions": positions_stub,
        "account_snapshot": account_snapshot_stub,
        "hyperliquid_client": hyperliquid_client_stub,
        "hyperliquid_poc": hyperliquid_poc_stub,
        "hyperliquid_poc.config": hyperliquid_config_stub,
    }
    previous_modules = {
        name: sys.modules.get(name)
        for name in module_stubs
    }

    for name, stub in module_stubs.items():
        sys.modules[name] = stub

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for name, previous in previous_modules.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous


reconciler = _load_isolated_reconciler()


class ReconciliationResultsTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(
            """
            CREATE TABLE system_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        self.conn.execute(
            """
            INSERT INTO system_state (key, value)
            VALUES ('current_cycle_id', 'cycle-1')
            """
        )
        self.conn.execute(
            """
            CREATE TABLE positions (
                position_id TEXT PRIMARY KEY,
                asset TEXT,
                direction TEXT,
                entry_price REAL,
                current_price REAL,
                stop_loss_price REAL,
                position_size REAL,
                opened_at TEXT,
                updated_at TEXT,
                status TEXT,
                unrealized_pnl REAL,
                realized_pnl REAL,
                cycle_opened TEXT,
                exchange_order_id TEXT,
                stop_loss_order_id TEXT,
                take_profit_order_id TEXT
            )
            """
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def add_local_position(
        self,
        *,
        position_id=None,
        asset="BTC",
        direction="LONG",
        size=1.0,
        stop_loss_order_id="101",
        take_profit_order_id="102",
        entry_price=100.0,
    ):
        self.conn.execute(
            """
            INSERT INTO positions (
                position_id,
                asset,
                direction,
                entry_price,
                current_price,
                position_size,
                opened_at,
                updated_at,
                status,
                unrealized_pnl,
                realized_pnl,
                cycle_opened,
                exchange_order_id,
                stop_loss_order_id,
                take_profit_order_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                position_id or f"position-{asset}",
                asset,
                direction,
                entry_price,
                entry_price,
                size,
                NOW.isoformat(),
                NOW.isoformat(),
                "OPEN",
                0.0,
                0.0,
                "cycle-1",
                "entry-1",
                stop_loss_order_id,
                take_profit_order_id,
            ),
        )
        self.conn.commit()

    def make_exchange_position(
        self,
        *,
        asset="BTC",
        signed_size=Decimal("1"),
        entry_price=Decimal("100"),
    ):
        return AccountPositionSnapshotV1(
            asset=asset,
            signed_size=signed_size,
            position_value=Decimal("100"),
            margin_used=Decimal("10"),
            margin_mode=MarginMode.CROSS,
            leverage=Decimal("1"),
            unrealized_pnl=Decimal("0"),
            entry_price=entry_price,
            liquidation_price=None,
        )

    def make_snapshot(
        self,
        *,
        positions=(),
        status=AccountNormalizationStatus.VALID,
        exchange_timestamp=NOW,
        errors=(),
    ):
        return AccountSnapshotV1(
            schema_version="1.0",
            snapshot_id="snapshot-1",
            account_address="0xaccount",
            environment=AccountEnvironment.MAINNET,
            source=AccountSource.HYPERLIQUID_CLEARINGHOUSE_STATE,
            exchange_timestamp=exchange_timestamp,
            received_at=NOW,
            account_value=Decimal("1000"),
            total_margin_used=Decimal("10"),
            withdrawable=Decimal("900"),
            asset_positions=tuple(positions),
            normalization_status=status,
            normalization_errors=tuple(errors),
        )

    def make_frontend_order(
        self,
        *,
        oid,
        asset="BTC",
        side="A",
        size="1",
        original_size=None,
        is_trigger=True,
        reduce_only=True,
        trigger_price="90",
    ):
        return {
            "oid": oid,
            "coin": asset,
            "side": side,
            "sz": size,
            "origSz": original_size if original_size is not None else size,
            "isTrigger": is_trigger,
            "triggerPx": trigger_price,
            "triggerCondition": "diagnostic only",
            "isPositionTpsl": False,
            "reduceOnly": reduce_only,
            "orderType": "Stop Market",
            "timestamp": int(NOW.timestamp() * 1000),
            "children": [],
        }

    def valid_long_orders(self, *, size="1"):
        return [
            self.make_frontend_order(
                oid=101,
                size=size,
                trigger_price="90",
            ),
            self.make_frontend_order(
                oid=102,
                size=size,
                trigger_price="110",
            ),
        ]

    def valid_short_orders(self, *, size="1"):
        return [
            self.make_frontend_order(
                oid=101,
                side="B",
                size=size,
                trigger_price="110",
            ),
            self.make_frontend_order(
                oid=102,
                side="B",
                size=size,
                trigger_price="90",
            ),
        ]

    def evaluate(self, snapshot, *, frontend_orders=()):
        return reconciler.reconcile(
            self.conn,
            account_snapshot=snapshot,
            fills=[],
            frontend_orders=frontend_orders,
            evaluated_at=NOW,
            max_snapshot_age_seconds=10,
            size_tolerance=Decimal("0"),
        )

    def persisted_result(self):
        row = self.conn.execute(
            """
            SELECT
                cycle_id,
                state,
                capability,
                snapshot_id,
                details_json,
                is_final
            FROM reconciliation_results
            ORDER BY evaluated_at DESC
            LIMIT 1
            """
        ).fetchone()
        self.assertIsNotNone(row)
        return {
            "cycle_id": row[0],
            "state": row[1],
            "capability": row[2],
            "snapshot_id": row[3],
            "details": json.loads(row[4]),
            "is_final": bool(row[5]),
        }

    def assert_result(self, result, *, state, capability):
        self.assertEqual(result.state.value, state)
        self.assertEqual(result.capability.value, capability)
        self.assertEqual(result.cycle_id, "cycle-1")
        stored = self.persisted_result()
        self.assertEqual(stored["cycle_id"], "cycle-1")
        self.assertEqual(stored["state"], state)
        self.assertEqual(stored["capability"], capability)
        self.assertEqual(stored["snapshot_id"], "snapshot-1")
        self.assertTrue(stored["is_final"])

    def assert_protection_failure(self, result, reason):
        self.assert_result(
            result,
            state="UNKNOWN",
            capability="NO_AUTOMATED_EXECUTION",
        )
        self.assertEqual(result.blocking_reason, reason)
        self.assertEqual(result.valid_until, result.evaluated_at)
        self.assertIn(
            reason,
            result.details["protection_validation"]["errors"],
        )

    def test_matching_positions_are_confirmed(self):
        self.add_local_position(size=1.0)
        result = self.evaluate(
            self.make_snapshot(
                positions=(self.make_exchange_position(),),
            ),
            frontend_orders=self.valid_long_orders(),
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )

    def test_empty_portfolio_needs_no_protection_endpoint(self):
        class FailingInfo:
            def frontend_open_orders(self, _address):
                raise AssertionError("frontend endpoint must not be called")

        with mock.patch.object(reconciler, "get_info", return_value=FailingInfo()):
            result = reconciler.reconcile(
                self.conn,
                account_snapshot=self.make_snapshot(),
                fills=[],
                evaluated_at=NOW,
            )

        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )
        self.assertEqual(
            result.details["protection_validation"]["status"],
            "NOT_REQUIRED",
        )

    def test_valid_short_protections_allow_open_and_reduce(self):
        self.add_local_position(direction="SHORT")
        result = self.evaluate(
            self.make_snapshot(
                positions=(
                    self.make_exchange_position(signed_size=Decimal("-1")),
                )
            ),
            frontend_orders=self.valid_short_orders(),
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )

    def test_missing_stop_loss_fails_closed(self):
        self.add_local_position()
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=self.valid_long_orders()[1:],
        )
        self.assert_protection_failure(result, "PROTECTION_MISSING")

    def test_missing_take_profit_fails_closed(self):
        self.add_local_position()
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=self.valid_long_orders()[:1],
        )
        self.assert_protection_failure(result, "PROTECTION_MISSING")

    def test_both_protections_missing_fail_closed(self):
        self.add_local_position()
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=[],
        )
        self.assert_protection_failure(result, "PROTECTION_MISSING")
        positions = result.details["protection_validation"]["positions"]
        self.assertFalse(positions[0]["stop_loss"]["observed"])
        self.assertFalse(positions[0]["take_profit"]["observed"])

    def test_null_stop_loss_id_fails_closed(self):
        self.add_local_position(stop_loss_order_id=None)
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=self.valid_long_orders(),
        )
        self.assert_protection_failure(result, "STOP_LOSS_ID_MISSING")

    def test_null_take_profit_id_fails_closed(self):
        self.add_local_position(take_profit_order_id=None)
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=self.valid_long_orders(),
        )
        self.assert_protection_failure(result, "TAKE_PROFIT_ID_MISSING")

    def test_wrong_asset_fails_closed(self):
        self.add_local_position()
        orders = self.valid_long_orders()
        orders[0]["coin"] = "ETH"
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=orders,
        )
        self.assert_protection_failure(result, "PROTECTION_ASSET_MISMATCH")

    def test_wrong_side_fails_closed(self):
        self.add_local_position()
        orders = self.valid_long_orders()
        orders[0]["side"] = "B"
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=orders,
        )
        self.assert_protection_failure(result, "PROTECTION_SIDE_INVALID")

    def test_non_trigger_order_fails_closed(self):
        self.add_local_position()
        orders = self.valid_long_orders()
        orders[0]["isTrigger"] = False
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=orders,
        )
        self.assert_protection_failure(result, "PROTECTION_NOT_TRIGGER")

    def test_non_reduce_only_order_fails_closed(self):
        self.add_local_position()
        orders = self.valid_long_orders()
        orders[0]["reduceOnly"] = False
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=orders,
        )
        self.assert_protection_failure(result, "PROTECTION_NOT_REDUCE_ONLY")

    def test_insufficient_remaining_size_fails_closed(self):
        self.add_local_position()
        orders = self.valid_long_orders()
        orders[0]["sz"] = "0.5"
        orders[0]["origSz"] = "1"
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=orders,
        )
        self.assert_protection_failure(result, "PROTECTION_SIZE_INSUFFICIENT")

    def test_larger_reduce_only_size_is_valid(self):
        self.add_local_position()
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=self.valid_long_orders(size="1.5"),
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )

    def test_wrong_trigger_direction_fails_closed(self):
        self.add_local_position()
        orders = self.valid_long_orders()
        orders[0]["triggerPx"] = "110"
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=orders,
        )
        self.assert_protection_failure(result, "PROTECTION_SEMANTICS_INVALID")

    def test_missing_exchange_entry_price_fails_closed(self):
        self.add_local_position()
        result = self.evaluate(
            self.make_snapshot(
                positions=(self.make_exchange_position(entry_price=None),)
            ),
            frontend_orders=self.valid_long_orders(),
        )
        self.assert_protection_failure(result, "PROTECTION_SEMANTICS_INVALID")

    def test_non_list_frontend_response_fails_closed(self):
        self.add_local_position()
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders={"orders": self.valid_long_orders()},
        )
        self.assert_protection_failure(result, "PROTECTION_RESPONSE_INVALID")

    def test_malformed_frontend_item_fails_closed(self):
        self.add_local_position()
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=[{"coin": "BTC"}],
        )
        self.assert_protection_failure(result, "PROTECTION_RESPONSE_INVALID")

    def test_frontend_api_exception_fails_closed(self):
        self.add_local_position()

        class FailingInfo:
            def frontend_open_orders(self, _address):
                raise RuntimeError("frontend unavailable")

        with mock.patch.object(reconciler, "get_info", return_value=FailingInfo()):
            result = reconciler.reconcile(
                self.conn,
                account_snapshot=self.make_snapshot(
                    positions=(self.make_exchange_position(),)
                ),
                fills=[],
                evaluated_at=NOW,
            )
        self.assertEqual(
            result.blocking_reason,
            "PROTECTION_OBSERVATION_ERROR",
        )
        self.assertEqual(
            result.capability,
            reconciler.ReconciliationCapability.NO_AUTOMATED_EXECUTION,
        )

    def test_duplicate_observed_oid_fails_closed(self):
        self.add_local_position()
        orders = self.valid_long_orders()
        orders.append(dict(orders[0]))
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=orders,
        )
        self.assert_protection_failure(result, "PROTECTION_OID_AMBIGUOUS")

    def test_unrelated_extra_order_does_not_block(self):
        self.add_local_position()
        orders = self.valid_long_orders()
        orders.append(self.make_frontend_order(oid=999, asset="ETH"))
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=orders,
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )

    def test_stale_different_oid_cannot_satisfy_protection(self):
        self.add_local_position(take_profit_order_id="777")
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=self.valid_long_orders(),
        )
        self.assert_protection_failure(result, "PROTECTION_MISSING")

    def test_multiple_local_rows_have_aggregate_protection_coverage(self):
        self.add_local_position(
            position_id="position-1",
            size=0.4,
            stop_loss_order_id="101",
            take_profit_order_id="102",
        )
        self.add_local_position(
            position_id="position-2",
            size=0.6,
            stop_loss_order_id="103",
            take_profit_order_id="104",
        )
        orders = [
            self.make_frontend_order(oid=101, size="0.4", trigger_price="90"),
            self.make_frontend_order(oid=102, size="0.4", trigger_price="110"),
            self.make_frontend_order(oid=103, size="0.6", trigger_price="90"),
            self.make_frontend_order(oid=104, size="0.6", trigger_price="110"),
        ]
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=orders,
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )

    def test_multiple_short_rows_remain_supported(self):
        self.add_local_position(
            position_id="short-position-1",
            direction="SHORT",
            size=0.4,
            stop_loss_order_id="201",
            take_profit_order_id="202",
        )
        self.add_local_position(
            position_id="short-position-2",
            direction="SHORT",
            size=0.6,
            stop_loss_order_id="203",
            take_profit_order_id="204",
        )
        orders = [
            self.make_frontend_order(
                oid=201, side="B", size="0.4", trigger_price="110"
            ),
            self.make_frontend_order(
                oid=202, side="B", size="0.4", trigger_price="90"
            ),
            self.make_frontend_order(
                oid=203, side="B", size="0.6", trigger_price="110"
            ),
            self.make_frontend_order(
                oid=204, side="B", size="0.6", trigger_price="90"
            ),
        ]
        result = self.evaluate(
            self.make_snapshot(
                positions=(
                    self.make_exchange_position(signed_size=Decimal("-1")),
                )
            ),
            frontend_orders=orders,
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )

    def test_opposite_local_directions_fail_closed_before_protection_lookup(self):
        self.add_local_position(
            position_id="long-position",
            direction="LONG",
            size=1.0,
            stop_loss_order_id="301",
            take_profit_order_id="302",
        )
        self.add_local_position(
            position_id="short-position",
            direction="SHORT",
            size=0.4,
            stop_loss_order_id="303",
            take_profit_order_id="304",
        )

        class FailingInfo:
            def frontend_open_orders(self, _address):
                raise AssertionError("protection lookup must not run")

        with mock.patch.object(reconciler, "get_info", return_value=FailingInfo()):
            result = reconciler.reconcile(
                self.conn,
                account_snapshot=self.make_snapshot(
                    positions=(
                        self.make_exchange_position(
                            signed_size=Decimal("0.6")
                        ),
                    )
                ),
                fills=[],
                evaluated_at=NOW,
                size_tolerance=Decimal("0"),
            )

        self.assert_protection_failure(result, "LOCAL_DIRECTION_AMBIGUOUS")
        self.assertEqual(
            result.details["local_direction_ambiguities"],
            [{"asset": "BTC", "directions": ["LONG", "SHORT"]}],
        )

    def test_opposite_local_directions_netting_to_zero_fail_closed(self):
        self.add_local_position(
            position_id="long-position",
            direction="LONG",
            size=0.5,
            stop_loss_order_id="401",
            take_profit_order_id="402",
        )
        self.add_local_position(
            position_id="short-position",
            direction="SHORT",
            size=0.5,
            stop_loss_order_id="403",
            take_profit_order_id="404",
        )
        result = reconciler.reconcile(
            self.conn,
            account_snapshot=self.make_snapshot(positions=()),
            fills=[],
            evaluated_at=NOW,
            size_tolerance=Decimal("0"),
        )

        self.assert_protection_failure(result, "LOCAL_DIRECTION_AMBIGUOUS")

    def test_protection_details_are_persisted(self):
        self.add_local_position()
        result = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=self.valid_long_orders(),
        )
        stored = self.persisted_result()
        protection = stored["details"]["protection_validation"]
        self.assertEqual(protection["status"], "CONFIRMED")
        self.assertEqual(protection["expected_count"], 2)
        self.assertEqual(
            protection["positions"][0]["stop_loss"]["expected_oid"],
            "101",
        )

    def test_different_size_is_size_mismatch(self):
        self.add_local_position(size=2.0)
        result = self.evaluate(
            self.make_snapshot(
                positions=(
                    self.make_exchange_position(
                        signed_size=Decimal("1"),
                    ),
                ),
            )
        )
        self.assert_result(
            result,
            state="SIZE_MISMATCH",
            capability="REDUCE_ONLY",
        )

    def test_exchange_only_is_detected(self):
        result = self.evaluate(
            self.make_snapshot(
                positions=(self.make_exchange_position(),),
            )
        )
        self.assert_result(
            result,
            state="EXCHANGE_ONLY",
            capability="REDUCE_ONLY",
        )

    def test_local_only_is_detected(self):
        self.add_local_position(size=1.0)
        result = self.evaluate(self.make_snapshot(positions=()))
        self.assert_result(
            result,
            state="LOCAL_ONLY",
            capability="REDUCE_ONLY",
        )

    def test_invalid_snapshot_is_unknown(self):
        result = self.evaluate(
            self.make_snapshot(
                status=AccountNormalizationStatus.INVALID,
                errors=("ASSET_POSITIONS_MISSING",),
            )
        )
        self.assert_result(
            result,
            state="UNKNOWN",
            capability="NO_AUTOMATED_EXECUTION",
        )

    def test_old_snapshot_is_stale(self):
        result = self.evaluate(
            self.make_snapshot(
                exchange_timestamp=NOW - timedelta(seconds=11),
            )
        )
        self.assert_result(
            result,
            state="STALE_DATA",
            capability="NO_AUTOMATED_EXECUTION",
        )

    def test_internal_snapshot_uses_time_after_acquisition(self):
        before = datetime(
            2026, 8, 7, 5, 12, 41, 198054, tzinfo=UTC
        )
        exchange_time = datetime(
            2026, 8, 7, 5, 12, 43, 294000, tzinfo=UTC
        )
        after = datetime(
            2026, 8, 7, 5, 12, 43, 597536, tzinfo=UTC
        )
        snapshot = self.make_snapshot(
            exchange_timestamp=exchange_time,
        )
        acquired = False

        def acquire_snapshot():
            nonlocal acquired
            acquired = True
            return snapshot

        def evaluation_time(_evaluated_at=None):
            self.assertTrue(acquired)
            return after

        self.assertLess(
            (before - exchange_time).total_seconds(),
            0,
        )

        with (
            mock.patch.object(
                reconciler,
                "get_account_snapshot",
                side_effect=acquire_snapshot,
            ),
            mock.patch.object(
                reconciler,
                "_evaluation_time",
                side_effect=evaluation_time,
            ),
        ):
            result = reconciler.reconcile(
                self.conn,
                fills=[],
                max_snapshot_age_seconds=10,
                size_tolerance=Decimal("0"),
            )

        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )
        self.assertEqual(result.evaluated_at, after)
        self.assertAlmostEqual(
            (after - exchange_time).total_seconds(),
            0.303536,
        )

    def test_future_snapshot_is_stale(self):
        result = self.evaluate(
            self.make_snapshot(
                exchange_timestamp=NOW + timedelta(microseconds=1),
            )
        )
        self.assert_result(
            result,
            state="STALE_DATA",
            capability="NO_AUTOMATED_EXECUTION",
        )
        self.assertLess(result.details["snapshot_age_seconds"], 0)
        self.assertEqual(result.valid_until, result.evaluated_at)

    def test_snapshot_exactly_ten_seconds_old_is_valid(self):
        result = self.evaluate(
            self.make_snapshot(
                exchange_timestamp=NOW - timedelta(seconds=10),
            )
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )

    def test_snapshot_older_than_ten_seconds_by_one_microsecond_is_stale(self):
        result = self.evaluate(
            self.make_snapshot(
                exchange_timestamp=(
                    NOW - timedelta(seconds=10, microseconds=1)
                ),
            )
        )
        self.assert_result(
            result,
            state="STALE_DATA",
            capability="NO_AUTOMATED_EXECUTION",
        )

    def test_slow_reconciliation_rechecks_freshness_before_result(self):
        snapshot = self.make_snapshot(exchange_timestamp=NOW)

        with mock.patch.object(
            reconciler,
            "_evaluation_time",
            side_effect=[
                NOW + timedelta(seconds=1),
                NOW + timedelta(seconds=11),
            ],
        ):
            result = reconciler.reconcile(
                self.conn,
                account_snapshot=snapshot,
                fills=[],
                max_snapshot_age_seconds=10,
                size_tolerance=Decimal("0"),
            )

        self.assert_result(
            result,
            state="STALE_DATA",
            capability="NO_AUTOMATED_EXECUTION",
        )
        self.assertEqual(
            result.evaluated_at,
            NOW + timedelta(seconds=11),
        )
        self.assertEqual(result.valid_until, result.evaluated_at)

    def test_frontend_observation_latency_is_caught_by_final_freshness_check(self):
        self.add_local_position()
        snapshot = self.make_snapshot(
            positions=(self.make_exchange_position(),),
            exchange_timestamp=NOW,
        )

        with mock.patch.object(
            reconciler,
            "_evaluation_time",
            side_effect=[
                NOW + timedelta(seconds=1),
                NOW + timedelta(seconds=11),
            ],
        ):
            result = reconciler.reconcile(
                self.conn,
                account_snapshot=snapshot,
                fills=[],
                frontend_orders=self.valid_long_orders(),
                max_snapshot_age_seconds=10,
                size_tolerance=Decimal("0"),
            )

        self.assert_result(
            result,
            state="STALE_DATA",
            capability="NO_AUTOMATED_EXECUTION",
        )

    def test_historical_take_profit_fill_closure_is_preserved(self):
        self.add_local_position()
        fill = {
            "coin": "BTC",
            "dir": "Close Long",
            "time": int(NOW.timestamp() * 1000),
            "oid": 102,
            "closedPnl": "12.5",
            "px": "110",
        }
        result = reconciler.reconcile(
            self.conn,
            account_snapshot=self.make_snapshot(),
            fills=[fill],
            evaluated_at=NOW,
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )
        self.assertEqual(
            result.details["automatic_actions"][0]["reconcile_status"],
            "TAKE_PROFIT",
        )

    def test_historical_stop_loss_fill_closure_is_preserved(self):
        self.add_local_position()
        fill = {
            "coin": "BTC",
            "dir": "Close Long",
            "time": int(NOW.timestamp() * 1000),
            "oid": 101,
            "closedPnl": "-4.5",
            "px": "90",
        }
        result = reconciler.reconcile(
            self.conn,
            account_snapshot=self.make_snapshot(),
            fills=[fill],
            evaluated_at=NOW,
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
        )
        self.assertEqual(
            result.details["automatic_actions"][0]["reconcile_status"],
            "STOP_LOSS",
        )

    def test_valid_until_is_limited_by_reconciliation_ttl(self):
        result = reconciler.reconcile(
            self.conn,
            account_snapshot=self.make_snapshot(exchange_timestamp=NOW),
            fills=[],
            evaluated_at=NOW,
            max_snapshot_age_seconds=100,
            size_tolerance=Decimal("0"),
        )

        self.assertEqual(
            result.valid_until,
            NOW + timedelta(
                seconds=reconciler.RECONCILIATION_TTL_SECONDS
            ),
        )

    def test_valid_until_is_limited_by_snapshot_freshness(self):
        result = self.evaluate(
            self.make_snapshot(
                exchange_timestamp=NOW - timedelta(seconds=8),
            )
        )

        self.assertEqual(
            result.valid_until,
            NOW + timedelta(seconds=2),
        )

    def test_invalid_snapshot_expires_at_evaluation_time(self):
        result = self.evaluate(
            self.make_snapshot(
                status=AccountNormalizationStatus.INVALID,
                errors=("ACCOUNT_STATE_INVALID",),
            )
        )

        self.assertEqual(result.state, reconciler.ReconciliationState.UNKNOWN)
        self.assertEqual(
            result.capability,
            reconciler.ReconciliationCapability.NO_AUTOMATED_EXECUTION,
        )
        self.assertEqual(result.evaluated_at, NOW)
        self.assertEqual(result.valid_until, NOW)

    def test_reconciliation_error_is_fail_closed(self):
        class FailingInfo:
            def user_fills(self, _address):
                raise RuntimeError("fills unavailable")

        with mock.patch.object(reconciler, "get_info", return_value=FailingInfo()):
            result = reconciler.reconcile(
                self.conn,
                account_snapshot=self.make_snapshot(),
                fills=None,
                evaluated_at=NOW,
                max_snapshot_age_seconds=10,
                size_tolerance=Decimal("0"),
            )

        self.assertEqual(result.state, reconciler.ReconciliationState.UNKNOWN)
        self.assertEqual(
            result.capability,
            reconciler.ReconciliationCapability.NO_AUTOMATED_EXECUTION,
        )
        self.assertEqual(result.blocking_reason, "RECONCILIATION_ERROR")
        self.assertEqual(result.evaluated_at, NOW)
        self.assertEqual(result.valid_until, NOW)

    def test_no_automated_execution_exits_20_after_evidence(self):
        result = reconciler._unknown_result(
            cycle_id="cycle-1",
            evaluated_at=NOW,
            blocking_reason="SNAPSHOT_INVALID",
            errors=["ACCOUNT_STATE_INVALID"],
        )
        events = []
        connection = mock.Mock()
        connection.close.side_effect = lambda: events.append("close")

        def record_print(*_args, **_kwargs):
            events.append("print")

        def exit_process(code):
            events.append(f"exit:{code}")
            raise SystemExit(code)

        with (
            mock.patch.object(
                reconciler.sqlite3,
                "connect",
                return_value=connection,
            ),
            mock.patch.object(
                reconciler,
                "reconcile",
                return_value=result,
            ),
            mock.patch("builtins.print", side_effect=record_print),
            mock.patch.object(
                reconciler.sys,
                "exit",
                side_effect=exit_process,
            ),
        ):
            with self.assertRaisesRegex(SystemExit, "20"):
                reconciler.main()

        self.assertEqual(events, ["close", "print", "exit:20"])

    def test_protection_failure_retains_exit_code_20(self):
        self.add_local_position()
        protection_failure = self.evaluate(
            self.make_snapshot(positions=(self.make_exchange_position(),)),
            frontend_orders=[],
        )
        connection = mock.Mock()

        with (
            mock.patch.object(
                reconciler.sqlite3,
                "connect",
                return_value=connection,
            ),
            mock.patch.object(
                reconciler,
                "reconcile",
                return_value=protection_failure,
            ),
        ):
            with self.assertRaisesRegex(SystemExit, "20"):
                reconciler.main()

        connection.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
