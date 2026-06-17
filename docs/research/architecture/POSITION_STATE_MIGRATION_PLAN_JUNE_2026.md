# MORPHO AGENTS — POSITION STATE MIGRATION PLAN

## June 2026

---

# PURPOSE

This document defines the migration plan emerging from the Position State Audit.

The objective is not to redesign the Economic Truth Hierarchy.

The objective is to remove transitional compatibility layers while preserving runtime behavior.

---

# CURRENT RUNTIME GRAPH

L1 Position State

position_state.json

↓

L3A Position Valuation

portfolio_state

↓

position_manager.py

↓

sqlite position_state

↓

StateManager

↓

dashboard

risk_manager

portfolio_health_manager

---

# TARGET RUNTIME GRAPH

L1 Position State

position_state.json

↓

L3A Position Valuation

portfolio_state

↓

StateManager

↓

dashboard

risk_manager

portfolio_health_manager

---

# MIGRATION PHILOSOPHY

The migration is not an ontology migration.

The ontology already appears correct.

The migration is a compatibility migration.

The objective is to remove adapters rather than redesign reality.

---

# PHASE 1

## StateManager Migration

Current:

FROM position_state

Target:

FROM portfolio_state

Internal compatibility adapter:

position_pnl

↓

unrealized_pnl

Validation:

Dashboard metrics unchanged.

Rollback:

Restore previous query.

---

# PHASE 2

## risk_manager Migration

Current:

FROM position_state

Target:

FROM portfolio_state

Validation:

Open positions unchanged.

Directional imbalance unchanged.

Rollback:

Restore previous query.

---

# PHASE 3

## portfolio_health_manager Migration

Current:

FROM position_state

Target:

FROM portfolio_state

Validation:

Health score unchanged.

Asset concentration unchanged.

Rollback:

Restore previous query.

---

# PHASE 4

## Adapter Deprecation

position_manager.py

Classification:

Compatibility Layer

Not:

* Source Of Truth
* Independent Domain

Deprecation conditions:

All consumers migrated.

Validation:

No runtime dependency remains.

---

# PHASE 5

## sqlite position_state Removal

Removal only after:

Zero runtime readers.

Validation:

grep -R "FROM position_state" . --include="*.py"

Expected:

No consumers.

---

# PHASE 6

## Semantic Alignment

Current:

portfolio_state

Actual role:

L3A Position Valuation

Future name:

position_valuation

Objective:

Align naming with semantic reality.

---

# PHASE 7

## L3B Portfolio State

Portfolio State will exist as a materialized runtime view.

It will answer:

"How does the portfolio look as a whole?"

Portfolio State will not own persistence.

Portfolio State will remain derived.

---

# VALIDATION PRINCIPLE

After every phase:

Validate

Observe

Continue

No multi-phase migrations.

No simultaneous refactors.

---

# FINAL OBSERVATION

The Position State Audit suggests that the primary debt is:

Compatibility Migration

rather than:

Architectural Ontology.

The Economic Truth Hierarchy appears largely aligned with runtime reality.

The migration should therefore be incremental, reversible, and evidence-driven.

