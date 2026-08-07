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
    hyperliquid_client_stub.get_info = lambda: None
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
        asset="BTC",
        direction="LONG",
        size=1.0,
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
                f"position-{asset}",
                asset,
                direction,
                100.0,
                100.0,
                size,
                NOW.isoformat(),
                NOW.isoformat(),
                "OPEN",
                0.0,
                0.0,
                "cycle-1",
                "entry-1",
                "sl-1",
                "tp-1",
            ),
        )
        self.conn.commit()

    def make_exchange_position(
        self,
        *,
        asset="BTC",
        signed_size=Decimal("1"),
    ):
        return AccountPositionSnapshotV1(
            asset=asset,
            signed_size=signed_size,
            position_value=Decimal("100"),
            margin_used=Decimal("10"),
            margin_mode=MarginMode.CROSS,
            leverage=Decimal("1"),
            unrealized_pnl=Decimal("0"),
            entry_price=Decimal("100"),
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

    def evaluate(self, snapshot):
        return reconciler.reconcile(
            self.conn,
            account_snapshot=snapshot,
            fills=[],
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

    def test_matching_positions_are_confirmed(self):
        self.add_local_position(size=1.0)
        result = self.evaluate(
            self.make_snapshot(
                positions=(self.make_exchange_position(),),
            )
        )
        self.assert_result(
            result,
            state="CONFIRMED",
            capability="OPEN_AND_REDUCE",
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


if __name__ == "__main__":
    unittest.main()
