# MORPHO OPERATIONAL MODEL

## PURPOSE

This document describes the operational architecture model of Morpho Agents.

Its objective is to explain:

* operational domains
* ownership boundaries
* Source Of Truth hierarchy
* state relationships
* governance flow
* enforcement flow

This document represents the current operational architecture during Pre-Deployment Stabilization.

---

# CORE ARCHITECTURAL MODEL

Morpho is evolving from:

loosely connected scripts

toward:

state-driven operational infrastructure.

The system is organized around:

* explicit ownership
* Source of Truth hierarchy
* derived operational states
* centralized governance
* runtime coordination

---

# ECONOMIC TRUTH HIERARCHY

Morpho distinguishes between:

Economic Truth

and

Derived Interpretation.

Current hierarchy:

L0

Sovereign Economic Truth

(Blockchain / Protocol State)

Future

---

L1

Operational Economic Truth

positions

(Source Of Truth)

---

L2

Historical Economic Truth

executions

(Immutable History)

---

L3

Derived Operational Interpretation

portfolio_state

(snapshot)

---

Important:

Historical Truth

≠

Operational Truth

Derived States

≠

Source Of Truth

---

# positions

Role:

Operational Source Of Truth.

Purpose:

Represent current deployed capital.

Owns:

* entry_price
* current_price
* position_size
* unrealized_pnl
* realized_pnl
* status
* updated_at

Does not represent:

* historical actions
* analytics
* opportunity intelligence

---

# executions

Role:

Immutable historical history.

Purpose:

* audit trail
* analytics
* research

Not operational truth.

Not an operational dependency.

---

# portfolio_state

Role:

Derived operational snapshot.

Consumes:

positions

Purpose:

Provide operational views and downstream consumers.

Must never become the Source Of Truth.

---

# OPERATIONAL FLOW

system_state

↓

safe_runner

↓

market_data_manager

↓

positions

↓

portfolio_state

↓

risk_manager

↓

portfolio_health_manager

↓

paper_portfolio

↓

analytics

---

# OPERATIONAL DOMAINS

## Runtime Coordination

Question:

Is the machine operational?

Owner:

system_state

Responsibilities:

* cycle coordination
* runtime flags

---

## Price Infrastructure

Question:

Can market prices be trusted?

Owner:

market_data_manager

Responsibilities:

* market refresh
* price retrieval
* freshness checks

---

## Economic State

Question:

What capital is deployed?

Owner:

positions

Responsibilities:

* exposure
* PnL
* position status

---

## Portfolio Interpretation

Question:

How should deployed capital be represented?

Owner:

portfolio_state

Responsibilities:

* derived snapshots
* downstream consumers

---

## Portfolio Health

Question:

Is deployed capital structurally healthy?

Owner:

portfolio_health_manager

Responsibilities:

* concentration analysis
* structural fragility
* deployment quality

---

## Risk

Question:

Is the environment dangerous?

Owner:

risk_manager

Responsibilities:

* exposure limits
* risk evaluation
* protection

---

## Governance

Question:

What actions are allowed?

Owner:

kill_switch_manager

Responsibilities:

* execution permissions
* persistence
* emergency protection

---

# GOVERNANCE FLOW

Operational domains should not directly manipulate execution.

Flow:

operational state

↓

domain manager

↓

evaluation

↓

governance recommendation

↓

kill_switch_manager

↓

safe_runner

---

# CENTRALIZED ENFORCEMENT

safe_runner.py represents the primary enforcement layer.

Execution can be halted when:

kill_switch_active = true

Governance survives:

* crashes
* restarts
* failures

---

# STATE MANAGER DIRECTION

StateManager should evolve toward:

* centralized read abstraction
* validated write gateway
* unified operational access layer

Direct access should gradually decrease over time.

---

# PHASE OBJECTIVE

Pre-Deployment Stabilization does not prioritize advanced intelligence.

Current objective:

* stable ownership
* runtime robustness
* observability
* governance safety
* operational simplicity

Infrastructure precedes intelligence.

---

# EMERGING MODEL

Morpho is evolving toward:

Operational Infrastructure for Opportunity Intelligence.

The objective is not strategy execution.

The objective is coordinated operational capability able to:

* evaluate opportunities
* protect capital
* monitor exposure
* coordinate governance
* preserve operational continuity
* evolve over time

