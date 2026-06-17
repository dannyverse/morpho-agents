
import sqlite3
import pandas as pd
import json
import tempfile
import os

from datetime import datetime

# =========================
# DATABASE
# =========================

conn = sqlite3.connect(
    "trading_system.db"
)

# =========================
# LOAD POSITIONS
# =========================

query = """

SELECT *

FROM portfolio_state


"""

positions_df = pd.read_sql_query(
    query,
    conn
)

# =========================
# BASIC METRICS
# =========================

position_count = len(
    positions_df
)

deployment_efficiency = 0

directional_bias = 0

max_asset_concentration = 0

alerts = []

# =========================
# EMPTY PORTFOLIO
# =========================

if position_count == 0:

    health_score = 100

    status = "HEALTHY"

# =========================
# ACTIVE PORTFOLIO
# =========================

else:

    # =====================
    # DIRECTIONAL BIAS
    # =====================


    # =====================
    # ASSET CONCENTRATION
    # =====================

    asset_counts = (
        positions_df["asset"]
        .value_counts(normalize=True)
        * 100
    )

    max_asset_concentration = (
        asset_counts.max()
    )

    # =====================
    # DEPLOYMENT EFFICIENCY
    # =====================

    deployment_efficiency = min(
        position_count * 5,
        100
    )

    # =====================
    # HEALTH SCORE
    # =====================

    health_score = 100

    health_score -= (
        directional_bias * 0.3
    )

    health_score -= (
        max_asset_concentration * 0.3
    )

    # =====================
    # STATUS
    # =====================

    if health_score >= 80:

        status = "HEALTHY"

    elif health_score >= 60:

        status = "WARNING"

    elif health_score >= 40:

        status = "UNSTABLE"

    else:

        status = "CRITICAL"

    # =====================
    # ALERTS
    # =====================

    if directional_bias > 80:

        alerts.append(
            "High directional bias"
        )

    if max_asset_concentration > 50:

        alerts.append(
            "High asset concentration"
        )

# =========================
# OUTPUT STATE
# =========================

state = {

    "schema_version": "1.0",

    "timestamp": str(
        datetime.now()
    ),

    "health_score": round(
        health_score,
        2
    ),

    "status": status,

    "metrics": {

        "position_count":
        position_count,

        "deployment_efficiency":
        round(
            deployment_efficiency,
            2
        ),

        "directional_bias":
        round(
            directional_bias,
            2
        ),

        "max_asset_concentration":
        round(
            max_asset_concentration,
            2
        )
    },

    "alerts": alerts,

    "derived_from":
    "position_state"
}

# =========================
# WRITE STATE
# =========================

with tempfile.NamedTemporaryFile(

    "w",

    delete=False

) as temp_file:

    json.dump(

        state,

        temp_file,

        indent=4
    )

    temp_path = (
        temp_file.name
    )

os.replace(

    temp_path,

    "portfolio_health_state.json"
)

# =========================
# OUTPUT
# =========================

print("\n")
print(
    "🏥 PORTFOLIO HEALTH"
)

print("=" * 50)

print("\n")

print(
    json.dumps(
        state,
        indent=4
    )
)

print("\n")
print(
    "✅ portfolio_health_state.json updated"
)

conn.close()


