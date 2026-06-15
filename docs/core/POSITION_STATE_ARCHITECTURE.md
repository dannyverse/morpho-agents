# POSITION STATE ARCHITECTURE

## PURPOSE

Defines the future canonical live position Source Of Truth for Morpho Agents.

This document establishes:

* live position semantics
* economic exposure semantics
* mark-to-market foundations
* reconciliation foundations
* governance visibility
* portfolio truthfulness

---

# CORE PRINCIPLE

position_state.json should represent:

```text id="ps4"
the canonical real-time economic state
of deployed capital
```

NOT:

* signal history
* execution history
* opportunity memory
* backtest memory

It represents:

```text id="ps5"
currently active economic exposure
```

---

# PRIMARY OBJECTIVES

position_state exists to provide:

* active exposure visibility
* live economic state
* mark-to-market valuation capability
* governance visibility
* reconciliation truthfulness
* operational observability

---

# IMPORTANT DISTINCTION

## signal_memory.csv

Represents:

```text id="ps6"
historical signal and execution memory
```

---

## position_state.json

Represents:

```text id="ps7"
live economic reality
```

This distinction is critical.

---

# FUTURE POSITION STATE MODEL

Example conceptual structure:

```json id="ps8"
{
  "BTC": {
    "status": "OPEN",
    "side": "LONG",
    "entry_price": 65000,
    "current_price": 66250,
    "quantity": 0.25,
    "notional_value": 16562.5,
    "unrealized_pnl": 312.5,
    "opened_at": "2026-06-15T08:00:00",
    "exchange": "hyperliquid",
    "confidence_score": 8.2
  }
}
```

---

# REQUIRED SEMANTICS

## status

Defines whether position is:

* OPEN
* CLOSED
* PARTIALLY_CLOSED

---

## entry_price

Canonical execution entry reference.

Required for:

* unrealized pnl
* reconciliation
* exposure truthfulness

---

## current_price

Latest trusted market valuation.

Derived from:

```text id="ps9"
Market Data Layer
```

---

## quantity

Canonical exposure amount.

Required for:

* mark-to-market valuation
* risk visibility
* governance awareness

---

## unrealized_pnl

Derived dynamically from:

```text id="ps10"
(current_price - entry_price)
*
quantity
```

Should NOT be manually persisted.

---

# GOVERNANCE IMPORTANCE

position_state eventually becomes critical for:

* exposure-aware governance
* risk-aware execution
* portfolio fragility analysis
* capital allocation visibility
* trust-aware operational control

---

# RECONCILIATION IMPORTANCE

position_state enables future reconciliation between:

```text id="ps11"
executions
↔ position_state
↔ portfolio_state
↔ governance_state
```

This becomes foundational for:

* economic truthfulness
* survivability
* auditability
* operational trust

---

# IMPORTANT ARCHITECTURAL PRINCIPLE

position_state should remain:

* lightweight
* human-readable
* operationally inspectable
* grep-friendly
* governance-oriented

Avoid:

* unnecessary abstraction
* hidden accounting layers
* opaque portfolio engines
* premature complexity

---

# CURRENT STATUS

As of June 2026:

```text id="ps12"
position_state
does not yet exist canonically
```

Current portfolio semantics are derived primarily from:

```text id="ps13"
signal_memory.csv
```

which represents:

```text id="ps14"
historical execution memory
```

rather than:

```text id="ps15"
live economic state
```

This distinction is intentional and now explicitly documented.

---

# LONG-TERM ROLE

position_state is expected to become:

```text id="ps16"
the economic Source Of Truth
for live deployed capital
```

and one of the central operational governance layers inside Morpho.

