import pandas as pd
import json
from datetime import datetime
import time

# =========================
# LOAD ACTIVE SHORTS
# =========================

t0 = time.perf_counter()

active = pd.read_sql_query(

    """
    SELECT
        sm.asset,
        sm.score,
        sm.persistence
    FROM signal_memory sm
    JOIN (
        SELECT
            asset,
            MAX(rowid) AS last_rowid
        FROM signal_memory
        WHERE direction = 'SHORT'
          AND persistence >= 10
        GROUP BY asset
    ) latest
    ON sm.rowid = latest.last_rowid
    """,

    __import__("sqlite3").connect(
        "trading_system.db"
    )
)

print(f"SQL: {time.perf_counter() - t0:.3f}s")
t1 = time.perf_counter()

# =========================
# LOAD PREVIOUS STATE
# =========================

try:

    with open(

        "opportunity_state.json",

        "r"

    ) as f:

        previous_state = json.load(f)

except:

    previous_state = {}
# =========================
# BUILD OPPORTUNITY STATE
# =========================

opportunities = {}

for _, row in active.iterrows():

    asset = row["asset"]

    persistence = row["persistence"]

    score = row["score"]

    # =========================
    # LIFECYCLE STAGE
    # =========================
    previous = previous_state.get(
    f"{asset}_SHORT"
    )

    previous_persistence = 0

    if previous:

        previous_persistence = previous.get(
        "persistence",
        0
    )

# =========================
# LIFECYCLE LOGIC
# =========================

    if previous is None:

        stage = "DETECTED"

    elif persistence > previous_persistence:

        stage = "STRENGTHENING"

    elif persistence == previous_persistence:

        stage = "ACTIVE"

    else:

        stage = "DECAYING"

    # =========================
    # OPPORTUNITY OBJECT
    # =========================

    opportunities[f"{asset}_SHORT"] = {

        "asset": asset,

        "direction": "SHORT",

        "persistence": int(persistence),

        "score": int(score),

        "lifecycle_stage": stage,

        "last_seen": str(
            datetime.utcnow()
        )
    }
# =========================
# RETIRED OPPORTUNITIES
# =========================

for key, previous in previous_state.items():

    if key not in opportunities:

        opportunities[key] = {

            "asset": previous["asset"],

            "direction": previous["direction"],

            "persistence": previous[
                "persistence"
            ],

            "score": previous["score"],

            "lifecycle_stage": "RETIRED",

            "last_seen": previous[
                "last_seen"
            ]
        }
# =========================
# SAVE STATE
# =========================

print(f"Processing: {time.perf_counter() - t1:.3f}s")
t2 = time.perf_counter()

with open(

    "opportunity_state.json",

    "w"

) as f:

    json.dump(

        opportunities,

        f,

        indent=4
    )

print(f"JSON: {time.perf_counter() - t2:.3f}s")

# =========================
# OUTPUT
# =========================

# =========================
# LIFECYCLE SUMMARY
# =========================

detected = 0
active_count = 0
strengthening = 0
decaying = 0
retired = 0

for value in opportunities.values():

    stage = value["lifecycle_stage"]

    if stage == "DETECTED":

        detected += 1

    elif stage == "ACTIVE":

        active_count += 1

    elif stage == "STRENGTHENING":

        strengthening += 1

    elif stage == "DECAYING":

        decaying += 1
    elif stage == "RETIRED":

        retired += 1   
print("\n🧠 OPPORTUNITY MONITOR\n")

print(
    f"Tracked Opportunities: "
    f"{len(opportunities)}"
)

print(f"Detected: {detected}")

print(f"Active: {active_count}")

print(
    f"Strengthening: "
    f"{strengthening}"
)

print(f"Decaying: {decaying}")
print(f"Retired: {retired}")
for key, value in opportunities.items():

    print(

        f"🟢 {key} | "

        f"{value['lifecycle_stage']} | "

        f"Persistence: {value['persistence']}"
    )
