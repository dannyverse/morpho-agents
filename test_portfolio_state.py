import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
PORTFOLIO_STATE_SCRIPT = PROJECT_ROOT / "portfolio_state.py"


class PortfolioStateRegressionTests(unittest.TestCase):
    def test_empty_open_positions_persists_empty_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "trading_system.db"

            conn = sqlite3.connect(db_path)

            conn.execute(
                """
                CREATE TABLE positions (
                    status TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE portfolio_state (
                    timestamp TEXT,
                    asset TEXT,
                    direction TEXT,
                    entry_price REAL,
                    current_price REAL,
                    leverage REAL,
                    position_size REAL,
                    unrealized_pnl REAL,
                    realized_pnl REAL,
                    status TEXT,
                    position_type TEXT
                )
                """
            )

            conn.execute(
                """
                INSERT INTO portfolio_state (
                    timestamp,
                    asset,
                    direction,
                    entry_price,
                    current_price,
                    leverage,
                    position_size,
                    unrealized_pnl,
                    realized_pnl,
                    status,
                    position_type
                )
                VALUES (
                    '2026-07-30 21:12:06',
                    'OLD',
                    'LONG',
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    0.0,
                    0.0,
                    'OPEN',
                    'DIRECTIONAL_LONG'
                )
                """
            )

            conn.commit()
            conn.close()

            result = subprocess.run(
                [sys.executable, str(PORTFOLIO_STATE_SCRIPT)],
                cwd=temp_path,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=result.stderr or result.stdout,
            )

            conn = sqlite3.connect(db_path)
            rows = conn.execute(
                "SELECT * FROM portfolio_state"
            ).fetchall()
            conn.close()

            self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
