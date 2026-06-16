# MORPHO AGENTS — ECONOMIC STATE ARCHITECTURE

## VERSION

June 2026

---

# PURPOSE

This document defines the Economic Truth Hierarchy of Morpho Agents.

Its purpose is to establish:

* economic reality ownership
* state ownership boundaries
* interpretation boundaries
* assessment boundaries
* governance information flow

This document defines ontology.

It does not define implementation.

---

# CORE PRINCIPLE

Morpho maintains a strict separation between:

Reality

and

Interpretation.

Reality describes what exists.

Interpretation describes what reality means.

These domains must remain separate.

---

# INFORMATION FLOW

Economic information flows in one direction:

Reality
↓
Interpretation
↓
Assessment
↓
Governance

Derived systems may inform decisions.

Derived systems may never redefine reality.

---

# ECONOMIC TRUTH HIERARCHY

## L0 — SOVEREIGN TRUTH

Represents external economic reality.

Examples:

* blockchain state
* protocol balances
* exchange positions
* custody balances

Characteristics:

* outside Morpho
* authoritative
* ultimate economic reality

When conflict exists:

Sovereign Truth takes precedence.

---

## L1 — POSITION STATE

Represents operational economic reality.

Answers:

What capital is currently deployed?

What is the current economic exposure of the system?

Contains:

* asset
* side
* quantity
* entry_price
* status
* exchange
* lifecycle information

Does NOT contain:

* unrealized pnl
* portfolio analytics
* risk scores
* opportunity scores
* derived interpretation

Position State is Morpho's canonical operational representation of live economic reality.

Position State owns exposure reality.

Derived systems may interpret Position State.

They may never redefine it.

Position State has a single authorized owner.

---

## L2 — EXECUTIONS

Represents historical truth.

Answers:

What happened?

Contains:

* approvals
* rejections
* executions
* historical decisions
* execution metadata

Executions are immutable historical memory.

Executions are not operational reality.

Executions are not live exposure.

### Historical Flow Principle

Executions are generated from operational events.

Executions preserve historical truth.

Executions do not participate in operational reality ownership.

Executions may be used for:

* auditing
* research
* analytics
* learning

Executions may never redefine Position State.

---

## L3A — POSITION VALUATION

Represents position-level economic interpretation.

Answers:

What are active positions currently worth?

Calculated from:

Position State
+
Market Data

Contains:

* current_price
* market_value
* unrealized_pnl
* unrealized_return
* exposure_value

Position Valuation is derived.

No economic reality is lost if Position Valuation is deleted and rebuilt.

Position Valuation may never modify Position State.

Reality flows downward.

Interpretation flows upward.

---

## L3B — PORTFOLIO STATE

Represents portfolio-level economic interpretation.

Answers:

How does the portfolio look as a whole?

Calculated from:

Position Valuation

Contains:

* total exposure
* gross exposure
* net exposure
* directional concentration
* asset concentration
* capital utilization
* portfolio drawdown

Portfolio State is Derived Interpretation.

Portfolio State is not Source Of Truth.

Portfolio State may inform operational decisions.

Portfolio State may never define economic reality.

Portfolio State is a derived materialized view.

Historical portfolio snapshots belong to paper_portfolio.

---

# L4 — ASSESSMENT DOMAINS

Assessment domains evaluate interpretation.

They do not define reality.

## Portfolio Health

Answers:

Is deployed capital structurally healthy?

## Risk State

Answers:

How dangerous is the current environment?

Assessment domains consume derived interpretation.

They do not own economic reality.

---

# L5 — GOVERNANCE

Governance answers:

What actions are allowed?

Governance consumes:

* Position State
* Position Valuation
* Portfolio State
* Portfolio Health
* Risk State

Governance may enforce decisions.

Governance may never redefine reality.

---

# CONSTITUTIONAL ALIGNMENT

This architecture implements:

* Principle 3 — Single Ownership
* Principle 4 — Historical Truth Is Not Live Truth
* Principle 5 — Derived Analytics Are Not Source Truth
* Principle 6 — Sovereign Truth Precedence
* Principle 9 — Observability Before Automation
* Principle 10 — Incremental Evolution
* Reality Ownership ≠ Transition Governance

---

# FINAL PRINCIPLE

Reality flows downward.

Interpretation flows upward.

Assessment evaluates interpretation.

Governance acts on assessment.

Derived systems may inform decisions.

They may never redefine reality.

