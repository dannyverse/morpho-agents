import os
import subprocess
import sys
import time
import sqlite3
from datetime import datetime
import uuid
from core.logger import logger
from notifier import notify

# =========================
# AUTONOMOUS SYSTEM LOOP
# =========================
notify(
    level="INFO",
    title="SYSTEM STARTUP",
    body="Morpho has started successfully.",
)

while True:

    try:
        logger.info("system_cycle_started")

        cycle_start = time.time()
        cycle_id = (
        f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        f"_{uuid.uuid4().hex[:8]}"
        )

        logger.info(
            "cycle_id_generated",
            cycle_id=cycle_id
        )
        conn = sqlite3.connect(
            "trading_system.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO system_state
            (key, value, updated_at)
            VALUES (?, ?, ?)
            """,
            (
                "current_cycle_id",
                cycle_id,
                str(datetime.utcnow())
            )
        )

        conn.commit()

        conn.close()
        # =========================
        # HEADER
        # =========================

        print("\n")
        print("=" * 60)

        
        

        

        
        
        
         

         

        
        
        

        print("\n")
        print("=" * 60)

        print(
            "🚀 AUTONOMOUS QUANT SYSTEM"
        )

        print("=" * 60)

        print("\n")

        print(
            f"🕒 Cycle Start: "
            f"{datetime.now()}"
        )

        # =========================
        # LOAD MARKET REGIME
        # =========================

        market_regime = "NEUTRAL"

        if os.path.exists(
            "market_regime.txt"
        ):

            with open(
                "market_regime.txt",
                "r"
            ) as f:

                market_regime = (
                    f.read().strip()
                )

        print("\n")

        print(
            f"🧠 Market Regime: "
            f"{market_regime}"
        )

        # =========================
        # REGIME MODE
        # =========================

        if market_regime == "DEFENSIVE":

            print(
                "🛡️ Defensive mode enabled"
            )

        elif market_regime == "AGGRESSIVE":

            print(
                "⚔️ Aggressive mode enabled"
            )

        else:

            print(
                "⚖️ Neutral mode enabled"
            )

        # =========================
        # SAFE ORCHESTRATION
        # =========================

        print("\n")

        print(
            "🛡️ Running safe runner..."
        )

        result = subprocess.run(
            [sys.executable, "safe_runner.py"]
        )

        exit_code = result.returncode

        # =========================
        # SAFE RUNNER STATUS
        # =========================

        print("\n")

        print(
            f"🧾 Safe Runner Exit Code: "
            f"{exit_code}"
        )

        if exit_code == 0:

            print(
                "✅ SYSTEM CYCLE COMPLETE"
            )

            logger.info(
                "system_cycle_completed"
            )

        elif exit_code == 10:

            print(
                "🛑 SYSTEM CYCLE ABORTED (Kill Switch)"
            )

            logger.info(
                "system_cycle_aborted"
            )

        else:

            print(
                f"❌ SYSTEM CYCLE FAILED ({exit_code})"
            )

            logger.error(
                "system_cycle_failed",
                exit_code=exit_code
            )

        # =========================
        # CYCLE COMPLETE
        # =========================

        cycle_end = time.time()

        cycle_duration = round(

            cycle_end -

            cycle_start,

            2
        )

        print("\n")


        print(
            f"⏱️ Cycle Duration: "
            f"{cycle_duration}s"
        )

        print("\n")

        print(
            "⏳ Sleeping 60 seconds..."
        )

        # =========================
        # SLEEP
        # =========================

        time.sleep(60)

    # =========================
    # GLOBAL EXCEPTION HANDLER
    # =========================

    except Exception as e:

        print("\n")
        print("=" * 60)

        print(
            "🚨 MASTER LOOP ERROR"
        )

        print("\n")

        print(str(e))

        notify(
            level="ERROR",
            title="MASTER LOOP ERROR",
            body=str(e),
        )

        print("\n")

        print(
            "🛡️ System survived exception"
        )

        print(
            "⏳ Restarting cycle in 60 seconds..."
        )

        time.sleep(60)
