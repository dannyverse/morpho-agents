# MORPHO BOOTSTRAP

## PURPOSE

This document exists to rapidly transfer project context to a new AI assistant, collaborator or future project session.

If you are entering this project for the first time:

Read:

1. PROJECT_STATUS.md
2. NEXT_SESSION.md
3. MORPHO_BOOTSTRAP.md

before making recommendations.

---

# WHAT MORPHO IS

Morpho Agents is NOT a trading bot.

Morpho Agents is an Opportunity Intelligence Platform.

The objective is not to optimize a single strategy.

The objective is to continuously improve the system's ability to discover, evaluate and exploit opportunities across digital markets.

Trading is only one execution mechanism.

---

# CORE THESIS

Digital markets increasingly favor machines over humans.

Reasons:

* 24/7 operation
* API-native infrastructure
* Global liquidity
* Massive information density
* Rapid opportunity decay
* Large search space

Morpho is being built around this thesis.

---

# NORTH STAR

The long-term goal is not to build a strategy.

The long-term goal is to build a machine capable of finding the next strategy.

The strategic asset is not a strategy.

The strategic asset is the discovery engine itself.

---

# CURRENT PROJECT PHASE

PHASE 0

FOUNDATION

Current Focus:

* State Architecture
* Ownership
* Observability
* Risk Foundation
* Infrastructure Stability

PHASE 0 IS NOT COMPLETE.

Do not recommend major architecture expansion before Foundation is complete.

---

# DEVELOPMENT PHILOSOPHY

Always prefer:

Architecture

>

Features

Observability

>

Optimization

Incremental Migrations

>

Large Refactors

Audit

>

Rewrite

Durability

>

Speed

---

# WORK SESSION PROTOCOL

Start Session:

1. Read PROJECT_STATUS.md
2. Read NEXT_SESSION.md
3. Review current objective

End Session:

1. Validate work
2. Update NEXT_SESSION.md
3. Update PROJECT_STATUS.md if architecture changed
4. Commit
5. Push

---

# STATE MODEL

system_state

Purpose:

Runtime state.

Contains:

* cycle_id
* runtime flags
* coordination state

---

position_state

Purpose:

Operational Source Of Truth.

Current Technical Owner:

position_manager.py

Future Owner:

Position Engine

---

portfolio_state

Purpose:

Derived State.

Must never become the primary source of truth.

Known Issue:

Circular dependency still exists.

---

paper_portfolio

Purpose:

Historical snapshots.

---

executions

Purpose:

Immutable history.

Audit trail.

Research dataset.

Not operational state.

---

# KNOWN ARCHITECTURAL DECISIONS

Confirmed:

# position_state

Single Source Of Truth

# portfolio_state

Derived State

# executions

Immutable History

# Opportunity Centric Architecture

Target Model

# Exchange Agnostic

Required Future State

# Strategy Agnostic

Required Future State

---

# CURRENT PRIORITIES

1. Observability Foundation Audit

Questions:

* Who owns system_log?
* What is system_status?
* What is the observability source of truth?

2. Circularity Resolution

position_state
↔
portfolio_state

3. Risk Foundation

4. Exchange Abstraction Design

---

# DO NOT RECOMMEND

Do not recommend:

* Complete rewrites
* Rebuilding the project from scratch
* Adding Meta Intelligence now
* Building Strategy Discovery now
* Adding complex AI layers before Foundation is complete

Foundation comes first.

---

# SUCCESS METRIC

Success is NOT measured primarily by short-term PnL.

Success is measured by the system's ability to:

* detect opportunities
* evaluate opportunities
* validate opportunities
* allocate capital
* monitor opportunities
* retire opportunities
* improve future opportunity discovery

---

# IF CONTEXT IS LOST

Ask the user for:

1. PROJECT_STATUS.md
2. NEXT_SESSION.md
3. MORPHO_BOOTSTRAP.md

Read them completely before making architectural recommendations.

