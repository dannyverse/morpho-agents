# RECONCILIATION_POLICY.md

Version: 1.0
Status: Draft
Scope: Exchange Reconciliation Layer
Owner: Morpho Architecture

---

# Purpose

Define the governance rules used by the Exchange Reconciler when the local operational state differs from the actual state of the exchange.

The reconciler is responsible for detecting inconsistencies.

The reconciler is NOT responsible for owning the lifecycle of positions.

The owner of position lifecycle remains:

positions.py

The reconciler may only request lifecycle actions through the public interface exposed by positions.py.

---

# Architectural Principles

1. Exchange is the source of truth for open positions.

2. SQLite is the operational cache used by Morpho.

3. Every automatic reconciliation must preserve economic reality.

4. Never fabricate trading history.

5. Never infer profit or loss without exchange evidence.

6. Unknown situations must always favor safety over automation.

---

# Reconciliation Flow

SQLite
↓

Exchange

↓

Detect Differences

↓

Classify Difference

↓

Apply Reconciliation Policy

↓

Delegate Lifecycle Action

↓

positions.py

---

# Classification: STOP_LOSS

Definition

The position is missing from the exchange.

A valid stop-loss order exists.

The stop-loss order status is FILLED.

Meaning

The exchange confirms that the position was closed by the stop-loss.

Action

- Close position.
- Delegate closure to positions.py.
- Preserve realized PnL.
- Update operational state.
- Log reconciliation.

Automatic

YES

---

# Classification: LEGACY

Definition

A position created during development that never became a real exchange position.

Typical characteristics include:

- exchange_order_id is NULL
- invalid or zero entry price
- no associated exchange orders
- identified as historical development residue

Meaning

This is not an economic event.

This is an administrative inconsistency.

Action

- Administrative closure.
- realized_pnl = 0
- Log administrative reconciliation.
- Never classify as STOP_LOSS.
- Never treat as a real trade outcome.

Automatic

YES

---

# Classification: UNKNOWN

Definition

SQLite and Exchange disagree.

The reconciler cannot determine why.

Meaning

Insufficient evidence.

Action

- Do NOT close.
- Do NOT modify SQLite.
- Generate warning.
- Require manual investigation.

Automatic

NO

---

# Ownership Rules

exchange_reconciler.py

Responsible for:

- Detect
- Inspect
- Classify
- Delegate

Never:

- Update positions directly.
- Execute lifecycle SQL.

positions.py

Responsible for:

- Open
- Close
- Lifecycle
- Position state transitions

Single owner of the Positions domain.

---

# Logging

Every reconciliation action must be logged.

Examples:

[RECONCILER] STOP_LOSS confirmed for BTC

[RECONCILER] Closed LEGACY position ARB (administrative reconciliation)

[RECONCILER] UNKNOWN reconciliation state for ETH - manual review required

---

# Safety Rules

Never close a position without evidence.

Never assume UNKNOWN equals STOP_LOSS.

Never fabricate realized PnL.

Never create trading history that did not occur.

Economic truth has priority over database consistency.

---

# Future Extensions

Possible future reconciliation states:

TAKE_PROFIT

MANUAL_CLOSE

LIQUIDATION

PARTIAL_CLOSE

CANCELLED

These states are outside the current deployment scope.

---

# Deployment Scope

Current automatic reconciliation:

✓ STOP_LOSS

✓ LEGACY

Manual reconciliation:

✓ UNKNOWN

No additional reconciliation types will be implemented before production deployment.
