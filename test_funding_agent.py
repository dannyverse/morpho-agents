import csv
import os
import runpy
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


class FundingAgentProductionBehaviorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script_path = Path(__file__).resolve().parent / "funding_agent.py"

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def market(name, *, funding, open_interest, volume):
        return (
            {"name": name},
            {
                "funding": str(funding),
                "openInterest": str(open_interest),
                "dayNtlVlm": str(volume),
            },
        )

    def run_agent(self, markets):
        assets = [asset for asset, _ in markets]
        contexts = [context for _, context in markets]
        response = mock.Mock()
        response.json.return_value = [
            {"universe": assets},
            contexts,
        ]

        requests_stub = types.ModuleType("requests")
        requests_stub.post = mock.Mock(return_value=response)
        pandas_stub = types.ModuleType("pandas")

        class DataFrame:
            def __init__(self, rows):
                self.rows = list(rows)

            @property
            def empty(self):
                return not self.rows

            def to_csv(self, path, *, mode, header, index):
                self.assert_false_index(index)
                fieldnames = list(self.rows[0]) if self.rows else []
                with open(path, mode, newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    if header:
                        writer.writeheader()
                    writer.writerows(self.rows)

            @staticmethod
            def assert_false_index(index):
                if index is not False:
                    raise AssertionError("funding CSV index contract changed")

        pandas_stub.DataFrame = DataFrame
        notify = mock.Mock()
        notifier_stub = types.ModuleType("notifier")
        notifier_stub.notify = notify

        previous_directory = Path.cwd()
        previous_requests = sys.modules.get("requests")
        previous_pandas = sys.modules.get("pandas")
        previous_notifier = sys.modules.get("notifier")
        sys.modules["requests"] = requests_stub
        sys.modules["pandas"] = pandas_stub
        sys.modules["notifier"] = notifier_stub
        os.chdir(self.workdir)
        try:
            try:
                runpy.run_path(str(self.script_path), run_name="__main__")
                exit_code = 0
            except SystemExit as exc:
                exit_code = exc.code
        finally:
            os.chdir(previous_directory)
            if previous_requests is None:
                sys.modules.pop("requests", None)
            else:
                sys.modules["requests"] = previous_requests
            if previous_pandas is None:
                sys.modules.pop("pandas", None)
            else:
                sys.modules["pandas"] = previous_pandas
            if previous_notifier is None:
                sys.modules.pop("notifier", None)
            else:
                sys.modules["notifier"] = previous_notifier

        return requests_stub.post, notify, exit_code

    @staticmethod
    def read_history(path):
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))

    def test_non_empty_quality_snapshot_persists_contract_without_push(self):
        post, notify, exit_code = self.run_agent([
            self.market(
                "BTC",
                funding="0.0001",
                open_interest=3_000_000,
                volume=6_000_000,
            ),
        ])

        self.assertEqual(exit_code, 0)
        post.assert_called_once_with(
            "https://api.hyperliquid.xyz/info",
            json={"type": "metaAndAssetCtxs"},
        )
        notify.assert_not_called()
        history = self.read_history(self.workdir / "funding_history.csv")
        self.assertEqual(
            list(history[0]),
            [
                "timestamp",
                "asset",
                "funding_apr",
                "open_interest",
                "volume",
            ],
        )
        self.assertEqual([row["asset"] for row in history], ["BTC"])
        self.assertAlmostEqual(float(history[0]["funding_apr"]), 87.6)
        self.assertEqual(float(history[0]["open_interest"]), 3_000_000)
        self.assertEqual(float(history[0]["volume"]), 6_000_000)

    def test_existing_quality_filters_are_preserved(self):
        _, notify, exit_code = self.run_agent([
            self.market(
                "PASS",
                funding="0.0001",
                open_interest=2_000_000,
                volume=5_000_000,
            ),
            self.market(
                "LOW_VOLUME",
                funding="0.0001",
                open_interest=3_000_000,
                volume=4_999_999,
            ),
            self.market(
                "LOW_OI",
                funding="0.0001",
                open_interest=1_999_999,
                volume=6_000_000,
            ),
            self.market(
                "APR_SPIKE",
                funding="0.0003",
                open_interest=3_000_000,
                volume=6_000_000,
            ),
        ])

        self.assertEqual(exit_code, 0)
        notify.assert_not_called()
        history = self.read_history(self.workdir / "funding_history.csv")
        self.assertEqual([row["asset"] for row in history], ["PASS"])
        self.assertAlmostEqual(float(history[0]["funding_apr"]), 87.6)

    def test_empty_quality_snapshot_preserves_success_exit_without_push(self):
        _, notify, exit_code = self.run_agent([
            self.market(
                "LOW_VOLUME",
                funding="0.0001",
                open_interest=3_000_000,
                volume=1_000_000,
            ),
        ])

        self.assertIsNone(exit_code)
        notify.assert_not_called()
        self.assertFalse((self.workdir / "funding_history.csv").exists())

    def test_existing_history_is_appended_without_duplicate_header(self):
        history_path = self.workdir / "funding_history.csv"
        history_path.write_text(
            "timestamp,asset,funding_apr,open_interest,volume\n"
            "2026-08-07 00:00:00,ETH,-10.0,4000000,7000000\n",
            encoding="utf-8",
        )

        _, notify, exit_code = self.run_agent([
            self.market(
                "BTC",
                funding="0.0001",
                open_interest=3_000_000,
                volume=6_000_000,
            ),
        ])

        self.assertEqual(exit_code, 0)
        notify.assert_not_called()
        history = self.read_history(history_path)
        self.assertEqual([row["asset"] for row in history], ["ETH", "BTC"])
        self.assertEqual(
            history_path.read_text(encoding="utf-8").count(
                "timestamp,asset,funding_apr,open_interest,volume"
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
