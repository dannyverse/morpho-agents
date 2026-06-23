# ARCHITECTURE PRINCIPLES — MORPHO AGENTS

## PURPOSE

This document records the architectural principles that have emerged through:

* implementation
* audits
* operational incidents
* multi-LLM architectural review
* iterative refinement

These principles guide architectural decisions.

This document is not a roadmap.

This document defines architectural doctrine.

---

# ARCHITECTURAL CONSENSUS

The following principles have repeatedly survived implementation and operational reality.

No principle is above reality.

---

# CONFIRMED ARCHITECTURAL PRINCIPLES

## Live State vs Historical Logs

Live operational state and historical records must remain separated.

Live state:

* mutable
* operational
* coordination-oriented

Historical logs:

* append-only
* analytical
* research-oriented

Historical records must never become operational dependencies.

---

## Single Owner Per State

Each operational domain should have:

* one owner
* one authoritative state
* one responsibility boundary

Ownership ambiguity produces fragility.

---

## Derived States Adapt To Source Of Truth

Derived states should adapt to Source of Truth maturity.

Source of Truth should not be distorted to satisfy derived states.

Current example:

market_data_manager

↓

positions

↓

portfolio_state

---

## Reality Ownership ≠ Transition Governance

Owning reality and governing transitions are different responsibilities.

Operational reality should remain simple.

Transition governance may evolve separately.

Future lifecycle engines govern transitions.

They do not own reality.

---

## Infrastructure Before Intelligence

Operational infrastructure should mature before higher intelligence layers.

Priority order:

Infrastructure

↓

Observability

↓

Risk

↓

Execution

↓

Optimization

↓

Intelligence

---

## Runtime Self-Protection

Runtime self-protection is part of core architecture.

The system should be capable of:

* detecting unsafe conditions
* persisting governance state
* halting execution safely
* recovering safely

without manual intervention.

---

## Incremental Migration Philosophy

Prefer:

incremental migrations

over

large refactors.

Pattern:

1. Introduce new owner.
2. Dual ownership temporarily if necessary.
3. Migrate consumers.
4. Remove legacy paths after validation.

Large simultaneous refactors increase risk.

---

## Operational Simplicity

Every module should be explainable in one sentence.

New components must solve a real problem.

Complexity is a cost.

Sophistication is not a goal.

---

## Discovery Is Not Authorization

Discoveries do not automatically change scope.

Interesting architecture is not authorization.

Real problems may be documented without immediate implementation.

---

## Reality Over Principles

Principles serve reality.

Reality does not serve principles.

No principle is above reality.

---

## Finite Audits, Infinite Learning

Audits are tools.

Reality is the objective.

Seek sufficient confidence.

Not perfect confidence.

---

# CONFIRMED OWNERSHIP DIRECTION

## system_state

Runtime coordination owner.

---

## market_data_manager

Price infrastructure owner.

---

## positions

Operational Source of Truth owner.

---

## portfolio_state

Derived operational snapshot.

---

## kill_switch_manager

Governance owner.

---

## portfolio_health_manager

Portfolio health owner.

---

# EMERGING DIRECTION

Morpho is evolving from:

loosely connected scripts

toward:

* coordinated infrastructure
* governance-aware runtime
* operational intelligence

without sacrificing simplicity.

---

# POST-DEPLOYMENT QUESTIONS

These questions are intentionally deferred.

## Lifecycle Semantics

OPEN

↓

CLOSED

↓

Liquidation

↓

Retirement

Transition governance remains future work.

---

## Reconciliation Maturity

Questions:

* corruption detection
* divergence detection
* sovereign truth enforcement

---

## Exchange Abstraction

Future requirement:

exchange-agnostic execution layer.

---

## Unified Risk Layer

Ownership and decomposition remain future work.

---

## Meta Intelligence

Deferred.

Infrastructure precedes intelligence.

---

# CORE PRINCIPLES

Single owner per state.

Derived states adapt to Source of Truth maturity.

Reality ownership ≠ transition governance.

Infrastructure before intelligence.

Operational simplicity over sophistication.

Discovery is not authorization.

Reality over principles.

No principle above reality.

Finite audits.

Infinite learning.

