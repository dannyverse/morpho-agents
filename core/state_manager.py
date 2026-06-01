import sqlite3
import pandas as pd

# =========================
# STATE MANAGER
# =========================

class StateManager:

    def __init__(
        self,
        db_name="trading_system.db"
    ):

        self.db_name = db_name

    # =========================
    # CONNECTION
    # =========================

    def get_connection(self):

        return sqlite3.connect(
            self.db_name
        )

    # =========================
    # CURRENT CYCLE
    # =========================

    def get_current_cycle_id(self):

        conn = self.get_connection()

        query = """

        SELECT value

        FROM system_state

        WHERE key='current_cycle_id'

        """

        df = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        if len(df) == 0:

            return None

        return df[
            "value"
        ].iloc[0]

    # =========================
    # POSITION STATE
    # =========================

    def get_position_state(self):

        conn = self.get_connection()

        query = """

        SELECT *

        FROM position_state

        """

        df = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        return df

    # =========================
    # OPEN POSITIONS
    # =========================

    def get_open_positions(self):

        positions = self.get_position_state()

        return len(
            positions
        )

    # =========================
    # PORTFOLIO METRICS
    # =========================
    # =========================
    # LATEST PORTFOLIO STATE
    # =========================

    def get_latest_portfolio_state(self):


        conn = self.get_connection()

        query = """

        SELECT *

        FROM paper_portfolio

        ORDER BY ROWID DESC

        LIMIT 1

        """

        df = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        if len(df) == 0:

            return None

        return df.iloc[0]
# =========================
# PORTFOLIO HISTORY
# =========================

    def get_portfolio_history(self):

        conn = self.get_connection()

        query = """

        SELECT *

        FROM paper_portfolio

        ORDER BY ROWID DESC

        LIMIT 50

        """

        df = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        return df

# =========================
# PORTFOLIO METRICS
# =========================

    def get_portfolio_metrics(self):

        positions = self.get_position_state()

        if len(positions) == 0:

            return {
                "open_positions": 0,
                "avg_pnl": 0,
                "best_trade": 0,
                "worst_trade": 0
            }

        return {
            "open_positions": len(positions),
            "avg_pnl": round(
                positions["position_pnl"].mean(),
                2
            ),
            "best_trade": round(
                positions["position_pnl"].max(),
                2
            ),
            "worst_trade": round(
                positions["position_pnl"].min(),
                2
            )
        }
    
            

    # =========================
    # PLACEHOLDERS
    # =========================

    def get_regime_state(self):

        return {
            "regime": "NEUTRAL",
            "confidence": 0.0
        }

    def get_agent_performance(self):

        return {}
