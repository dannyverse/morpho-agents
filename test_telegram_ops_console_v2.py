import importlib.util
import json
import sqlite3
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from ops_command_router import CommandRequest, OpsCommandRouter
from ops_read_providers import Availability, OpsReadProviders, ProviderResult


UTC = timezone.utc
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)


class OpsConsoleFixture(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "trading_system.db"
        self.runtime_path = self.root / "runtime_state.json"
        self.kill_path = self.root / "kill_switch_state.json"
        self.health_path = self.root / "portfolio_health_state.json"
        self.providers = OpsReadProviders(
            db_path=self.db_path,
            runtime_state_path=self.runtime_path,
            kill_switch_path=self.kill_path,
            portfolio_health_path=self.health_path,
            now=lambda: NOW,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_json(self, path, data):
        path.write_text(json.dumps(data), encoding="utf-8")

    def write_runtime(self, *, status="HEALTHY", cycle="cycle-1"):
        self.write_json(self.runtime_path, {
            "cycle_id": cycle,
            "heartbeat_timestamp": NOW.isoformat(),
            "system_status": status,
            "runtime_mode": "NORMAL",
            "active_modules": ["positions.py", "risk_manager.py"],
            "failed_modules": [],
            "last_error": None,
            "heartbeat_ok": True,
            "cycle_duration_seconds": 2.5,
            "last_successful_cycle": cycle,
        })

    def write_kill_switch(self, *, active=False):
        self.write_json(self.kill_path, {
            "kill_switch_active": active,
            "activation_timestamp": NOW.isoformat() if active else None,
            "deactivation_timestamp": None,
            "reason": "TEST" if active else None,
            "activated_by": "risk_manager" if active else None,
            "deactivated_by": None,
            "deactivation_reason": None,
        })

    def write_health(self):
        self.write_json(self.health_path, {
            "schema_version": "1.0",
            "timestamp": NOW.isoformat(),
            "health_score": 85,
            "status": "HEALTHY",
            "metrics": {
                "position_count": 1,
                "deployment_efficiency": 5,
                "directional_bias": 10,
                "max_asset_concentration": 20,
            },
            "alerts": [],
            "derived_from": "portfolio_state",
        })

    def create_db(self, *, optional_position_columns=False, expired=False):
        conn = sqlite3.connect(self.db_path)
        optional = """
            , exchange_order_id TEXT
            , stop_loss_order_id TEXT
            , take_profit_order_id TEXT
        """ if optional_position_columns else ""
        conn.execute(f"""
            CREATE TABLE positions (
                position_id TEXT PRIMARY KEY,
                asset TEXT,
                direction TEXT,
                entry_price REAL,
                current_price REAL,
                position_size REAL,
                opened_at TEXT,
                updated_at TEXT,
                unrealized_pnl REAL,
                realized_pnl REAL,
                cycle_opened TEXT,
                status TEXT
                {optional}
            )
        """)
        conn.execute("""
            CREATE TABLE reconciliation_results (
                reconciliation_id TEXT PRIMARY KEY,
                cycle_id TEXT,
                state TEXT,
                capability TEXT,
                snapshot_id TEXT,
                snapshot_timestamp TEXT,
                evaluated_at TEXT,
                valid_until TEXT,
                blocking_reason TEXT,
                details_json TEXT,
                is_final INTEGER
            )
        """)
        valid_until = NOW - timedelta(seconds=1) if expired else NOW + timedelta(seconds=10)
        conn.execute("""
            INSERT INTO reconciliation_results (
                reconciliation_id, cycle_id, state, capability,
                snapshot_timestamp, evaluated_at, valid_until,
                details_json, is_final
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "rec-1", "cycle-1", "CONFIRMED", "OPEN_AND_REDUCE",
            NOW.isoformat(), NOW.isoformat(), valid_until.isoformat(), "{}", 1,
        ))
        conn.commit()
        conn.close()

    def insert_position(self, *, optional=False):
        conn = sqlite3.connect(self.db_path)
        fields = [
            "position_id", "asset", "direction", "entry_price",
            "current_price", "position_size", "opened_at", "updated_at",
            "unrealized_pnl", "realized_pnl", "cycle_opened", "status",
        ]
        values = [
            "position-1", "BTC", "LONG", 100.0, 110.0, 0.1,
            NOW.isoformat(), NOW.isoformat(), 10.0, 0.0, "cycle-1", "OPEN",
        ]
        if optional:
            fields.extend([
                "exchange_order_id",
                "stop_loss_order_id",
                "take_profit_order_id",
            ])
            values.extend(["entry-1", "sl-1", "tp-1"])
        placeholders = ",".join("?" for _ in values)
        conn.execute(
            f"INSERT INTO positions ({','.join(fields)}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        conn.close()


class ProviderSafetyTest(OpsConsoleFixture):
    def test_missing_database_is_unavailable_and_not_created(self):
        self.assertEqual(self.providers.positions().availability, Availability.UNAVAILABLE)
        self.assertEqual(self.providers.reconciliation().availability, Availability.UNAVAILABLE)
        self.assertFalse(self.db_path.exists())

    def test_missing_json_is_unavailable_and_not_created(self):
        self.assertEqual(self.providers.runtime().availability, Availability.UNAVAILABLE)
        self.assertEqual(self.providers.kill_switch().availability, Availability.UNAVAILABLE)
        self.assertFalse(self.runtime_path.exists())
        self.assertFalse(self.kill_path.exists())

    def test_malformed_json_is_unavailable_and_unchanged(self):
        self.runtime_path.write_text("{broken", encoding="utf-8")
        before = self.runtime_path.read_bytes()
        self.assertEqual(self.providers.runtime().availability, Availability.UNAVAILABLE)
        self.assertEqual(self.runtime_path.read_bytes(), before)

    def test_provider_queries_do_not_write_database(self):
        self.create_db()
        before = self.db_path.read_bytes()
        self.providers.positions()
        self.providers.reconciliation()
        self.assertEqual(self.db_path.read_bytes(), before)

    def test_provider_connections_are_explicitly_closed(self):
        self.create_db()
        for operation in (
            self.providers.positions,
            self.providers.reconciliation,
        ):
            with self.subTest(operation=operation.__name__):
                connection = self.providers._connect_read_only()
                with mock.patch.object(
                    self.providers,
                    "_connect_read_only",
                    return_value=connection,
                ):
                    operation()
                with self.assertRaises(sqlite3.ProgrammingError):
                    connection.execute("SELECT 1")


class ProviderBehaviorTest(OpsConsoleFixture):
    def test_positions_without_optional_columns(self):
        self.create_db()
        self.insert_position()
        result = self.providers.positions()
        self.assertTrue(result.available)
        self.assertNotIn("exchange_order_id", result.data[0])

    def test_positions_with_optional_columns(self):
        self.create_db(optional_position_columns=True)
        self.insert_position(optional=True)
        result = self.providers.positions()
        self.assertEqual(result.data[0]["exchange_order_id"], "entry-1")

    def test_reconciliation_expiry_uses_valid_until(self):
        self.create_db(expired=True)
        result = self.providers.reconciliation()
        self.assertTrue(result.data["expired"])

    def test_risk_sources_are_limited_to_approved_fields(self):
        self.write_kill_switch()
        self.write_health()
        self.assertNotIn("risk_status", self.providers.portfolio_health().data)
        self.assertNotIn("governance_flags", self.providers.portfolio_health().data)


class RouterTest(OpsConsoleFixture):
    def setUp(self):
        super().setUp()
        self.write_runtime()
        self.write_kill_switch()
        self.write_health()
        self.create_db()
        self.router = OpsCommandRouter(self.providers)

    def route(self, text):
        return self.router.route(CommandRequest(text=text, chat_id="1"))

    def test_supported_commands(self):
        for command, heading in (
            ("/status", "MORPHO STATUS"),
            ("/health", "MORPHO HEALTH"),
            ("/positions", "OPEN POSITIONS"),
            ("/risk", "MORPHO RISK"),
            ("/help", "MORPHO OPS CONSOLE"),
        ):
            with self.subTest(command=command):
                self.assertIn(heading, self.route(command))

    def test_command_normalization(self):
        self.assertIn("MORPHO STATUS", self.route(" /STATUS "))
        self.assertIn("MORPHO HEALTH", self.route("/health@MorphoBot"))

    def test_unknown_arguments_and_opportunities_are_rejected(self):
        self.assertIn("Unknown command", self.route("/unknown"))
        self.assertIn("Arguments are not supported", self.route("/status now"))
        self.assertIn("Unknown command", self.route("/opportunities"))

    def test_help_is_exact_catalog(self):
        response = self.route("/help")
        for command in ("/status", "/health", "/positions", "/risk", "/help"):
            self.assertIn(command, response)
        self.assertIn("Read-only operational console.", response)
        self.assertIn("No trading actions are available.", response)

    def test_status_handles_partial_sources(self):
        self.kill_path.unlink()
        response = self.route("/status")
        self.assertIn("Kill Switch: UNAVAILABLE", response)
        self.assertIn("Runtime: HEALTHY", response)

    def test_status_initializing_and_cycle_mismatch(self):
        self.write_runtime(status="INITIALIZING", cycle="cycle-2")
        response = self.route("/status")
        self.assertIn("Cycle State: IN PROGRESS", response)
        self.assertIn("Cycle Mismatch", response)

    def test_status_and_positions_show_expired_reconciliation(self):
        self.db_path.unlink()
        self.create_db(expired=True)
        self.assertIn("Reconciliation Expired: YES", self.route("/status"))
        self.assertIn("Exchange Confirmation: EXPIRED", self.route("/positions"))

    def test_positions_cycle_mismatch_is_not_current(self):
        self.write_runtime(cycle="cycle-2")
        response = self.route("/positions")
        self.assertIn("Cycle Mismatch", response)
        self.assertIn("Exchange Confirmation: CYCLE MISMATCH", response)
        self.assertNotIn("Exchange Confirmation: CURRENT", response)

    def test_positions_zero_and_open(self):
        self.assertIn("No open local positions.", self.route("/positions"))
        self.insert_position()
        response = self.route("/positions")
        self.assertIn("BTC · LONG", response)
        self.assertIn("Size: 0.1", response)

    def test_positions_reconciliation_unavailable(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM reconciliation_results")
        conn.commit()
        conn.close()
        self.assertIn("Exchange Confirmation: UNAVAILABLE", self.route("/positions"))

    def test_risk_sources_render_independently(self):
        self.health_path.unlink()
        response = self.route("/risk")
        self.assertIn("Kill Switch: INACTIVE", response)
        self.assertIn("Portfolio Health: UNAVAILABLE", response)
        self.write_health()
        self.kill_path.unlink()
        response = self.route("/risk")
        self.assertIn("Kill Switch: UNAVAILABLE", response)
        self.assertIn("Portfolio Health: HEALTHY", response)
        self.assertNotIn("Risk Status", response)
        self.assertNotIn("governance_flags", response)

    def test_unexpected_router_error_is_logged_and_hidden(self):
        with mock.patch.object(
            self.providers,
            "runtime",
            side_effect=RuntimeError("private failure detail"),
        ):
            with self.assertLogs("ops_command_router", level="ERROR") as logs:
                response = self.route("/health")
        self.assertEqual(response, "Operational data is temporarily unavailable.")
        self.assertTrue(any("unexpected_ops_command_error" in item for item in logs.output))
        self.assertNotIn("private failure detail", response)


def load_telegram_interface():
    requests_stub = types.ModuleType("requests")
    requests_stub.RequestException = type("RequestException", (Exception,), {})
    requests_stub.post = mock.Mock()
    requests_stub.get = mock.Mock()
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda: None
    previous = {
        "requests": sys.modules.get("requests"),
        "dotenv": sys.modules.get("dotenv"),
    }
    sys.modules["requests"] = requests_stub
    sys.modules["dotenv"] = dotenv_stub
    try:
        path = Path(__file__).resolve().parent / "telegram_interface.py"
        spec = importlib.util.spec_from_file_location("_test_telegram_interface", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, value in previous.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


class TelegramInterfaceTest(unittest.TestCase):
    def setUp(self):
        self.interface = load_telegram_interface()
        self.interface.CHAT_ID = "123"
        self.interface.TOKEN = "token"

    def test_update_routes_without_real_telegram(self):
        router = mock.Mock()
        router.route.return_value = "response"
        sender = mock.Mock()
        update = {
            "update_id": 7,
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "text": "/status",
            },
        }
        self.interface.process_update(update, router, sender)
        request = router.route.call_args.args[0]
        self.assertEqual(request.text, "/status")
        self.assertEqual(request.chat_id, "123")
        self.assertEqual(request.user_id, "456")
        sender.assert_called_once_with("response", "123")

    def test_malformed_and_unauthorized_updates_are_ignored(self):
        router = mock.Mock()
        sender = mock.Mock()
        self.interface.process_update({}, router, sender)
        self.interface.process_update(
            {"message": {"chat": {"id": 999}, "text": "/status"}},
            router,
            sender,
        )
        router.route.assert_not_called()
        sender.assert_not_called()

    def test_transport_failures_are_logged_without_raising(self):
        error = self.interface.requests.RequestException("network")
        self.interface.requests.post.side_effect = error
        self.interface.requests.get.side_effect = error
        with self.assertLogs(self.interface.logger, level="WARNING") as logs:
            self.assertFalse(self.interface.send_message("response", "123"))
            self.assertIsNone(self.interface.get_updates())
        self.assertTrue(any("telegram_send_failed" in item for item in logs.output))
        self.assertTrue(any("telegram_poll_failed" in item for item in logs.output))
        self.assertFalse(any("token" in item for item in logs.output))
        self.assertFalse(any("response" in item for item in logs.output))

    def test_malformed_and_unauthorized_updates_advance_offset(self):
        router = mock.Mock()
        sender = mock.Mock()
        updates = [
            {"update_id": 10, "message": "malformed"},
            {
                "update_id": 11,
                "message": {"chat": {"id": 999}, "text": "/status"},
            },
        ]
        offset = self.interface.process_updates(updates, None, router, sender)
        self.assertEqual(offset, 12)
        router.route.assert_not_called()
        sender.assert_not_called()

    def test_authorized_update_is_at_most_once_when_send_fails(self):
        router = mock.Mock()
        router.route.return_value = "response"
        sender = mock.Mock(return_value=False)
        update = {
            "update_id": 20,
            "message": {"chat": {"id": 123}, "text": "/status"},
        }
        offset = self.interface.process_updates([update], None, router, sender)
        self.assertEqual(offset, 21)
        router.route.assert_called_once()
        sender.assert_called_once()

    def test_unexpected_update_failure_is_logged_and_offset_advances(self):
        router = mock.Mock()
        router.route.return_value = "response"
        sender = mock.Mock(side_effect=RuntimeError("send failure"))
        update = {
            "update_id": 30,
            "message": {"chat": {"id": 123}, "text": "/status"},
        }
        with self.assertLogs(self.interface.logger, level="WARNING") as logs:
            offset = self.interface.process_updates([update], None, router, sender)
        self.assertEqual(offset, 31)
        self.assertTrue(
            any("telegram_update_processing_failed" in item for item in logs.output)
        )


if __name__ == "__main__":
    unittest.main()
