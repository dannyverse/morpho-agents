# POSITION_STATE_ARCHITECTURE.md

# PURPOSE

This document defines the official architectural philosophy, ownership boundaries, and operational semantics of `position_state`.

This is a Foundation-level architectural definition.

Its purpose is to:

* establish canonical Source Of Truth boundaries
* prevent schema drift
* preserve operational clarity
* guide future migrations
* define what belongs inside operational truth vs derived intelligence

Core principle:

`position_state` should remain operationally sufficient without becoming analytically inflated.

---

# CORE DEFINITION

`position_state` represents:

The minimum operationally sufficient truth of deployed capital.

A position is:

A deployed capital unit with enough operational identity to:

* be monitored
* be governed
* be paused
* be closed
* be recovered
* be audited

No more.
No less.

---

# IMPORTANT DISCOVERY

Morpho is NOT fundamentally a LONG/SHORT trading system.

Morpho is fundamentally:

An opportunity intelligence and capital deployment system.

Therefore, positions may eventually represent:

* directional trades
* lending positions
* yield positions
* liquidity provision
* arbitrage opportunities
* prediction market exposure
* funding capture
* future unknown opportunity types

The Source Of Truth must remain flexible enough to support this evolution.

---

# ARCHITECTURAL PRINCIPLE

The purpose of `position_state` is NOT:

* portfolio analysis
* governance reasoning
* health evaluation
* concentration calculations
* derived intelligence

Those belong to:

* portfolio_health_state
* risk_state
* governance_state
* future opportunity intelligence layers

`position_state` exists to store operational execution truth.

---

# OFFICIAL SOURCE OF TRUTH BOUNDARY

## BELONGS INSIDE position_state

Operational identity:

* asset
* position_type
* status

Execution facts:

* entry_price
* current_price
* position_size
* position_pnl

Lifecycle identity:

* opened_at
* updated_at

---

## DOES NOT BELONG INSIDE position_state

Derived analytics:

* health_score
* concentration metrics
* exposure clustering
* risk scores
* governance recommendations
* portfolio aggregates
* imbalance calculations

These belong to derived operational states.

---

# POSITION TYPE PHILOSOPHY

`position_type` replaces narrow LONG/SHORT assumptions.

Examples:

* DIRECTIONAL_LONG
* DIRECTIONAL_SHORT
* YIELD
* LENDING
* LP
* ARBITRAGE
* FUNDING_CAPTURE
* PREDICTION

Important principle:

Morpho should remain opportunity-centric rather than trading-centric.

---

# STATUS PHILOSOPHY

`status` represents explicit operational lifecycle state.

Examples:

* OPEN
* CLOSED
* LIQUIDATED
* PAUSED
* FAILED

Important principle:

Lifecycle identity should remain explicit rather than inferred.

Without explicit lifecycle state:

* governance becomes ambiguous
* recovery becomes dangerous
* runtime observability degrades

---

# MINIMAL OPERATIONAL SUFFICIENCY

The goal is NOT:

* maximal richness
* maximal abstraction
* institutional complexity

The goal is:

Minimal operational sufficiency.

The Source Of Truth should contain:

* enough operational identity for safe system behavior
* but not derived intelligence

---

# CURRENT RECOMMENDED PHASE 0+ SCHEMA

```sql id="c9v2px"
CREATE TABLE position_state (

    position_id     TEXT PRIMARY KEY,

    cycle_id        TEXT,

    asset           TEXT,

    position_type   TEXT,

    entry_price     REAL,

    current_price   REAL,

    position_size   REAL,

    position_pnl    REAL,

    status          TEXT,

    opened_at       TEXT,

    updated_at      TEXT
)
```

---

# IMPORTANT DESIGN DECISION

The following are intentionally NOT included yet:

* strategy_id
* executor_id
* opportunity_id

Reason:

These concepts are not yet operationally mature enough to justify Source Of Truth inclusion.

Adding them now would risk premature abstraction.

---

# RELATIONSHIP WITH DERIVED STATES

`position_state`
↓
provides operational truth to
↓

* portfolio_health_state
* risk_state
* governance_state
* future opportunity intelligence systems

Derived states must adapt to Source Of Truth maturity.

The Source Of Truth should NOT expand prematurely to satisfy derived states.

---

# OPERATIONAL PHILOSOPHY

Operational simplicity is prioritized over architectural sophistication.

The system should remain:

* understandable
* observable
* mentally navigable
* operable by a single knowledgeable operator

Complexity should emerge organically from operational necessity.

Not from architectural aesthetics.

---

# CURRENT FOUNDATION CONCLUSION

Current architectural direction:

Minimal Source Of Truth
+
Operational identity essentials
+
Rich derived operational states

This is considered the healthiest long-term balance for Morpho evolution.

