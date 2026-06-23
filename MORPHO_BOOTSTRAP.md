# MORPHO BOOTSTRAP

## PURPOSE

This document exists to rapidly transfer project context to a new AI assistant, collaborator or future project session.

If you are entering this project for the first time:

Read:

1. DEPLOYMENT_CONTRACT.md
2. PROJECT_STATUS.md
3. NEXT_SESSION.md
4. MORPHO_BOOTSTRAP.md

before making recommendations.

The contract governs scope.

Reality governs architecture.

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

PRE-DEPLOYMENT STABILIZATION

Current focus:

* Ownership
* Observability
* Risk Foundation
* Infrastructure Stability

Foundation remains more important than expansion.

Do not recommend major architecture expansion before deployment.

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

Reality

>

Theory

---

# WORK SESSION PROTOCOL

Start Session:

1. Read DEPLOYMENT_CONTRACT.md
2. Read PROJECT_STATUS.md
3. Read NEXT_SESSION.md

Review current objective.

End Session:

1. Validate work
2. Update NEXT_SESSION.md
3. Update PROJECT_STATUS.md if reality changed
4. Commit
5. Push

---

# STATE MODEL

## system_state

Purpose:

Runtime coordination.

Contains:

* cycle_id
* runtime flags

---

## market_data_manager

Purpose:

Price infrastructure.

Owns:

* refresh_market_data()
* get_price()
* market data freshness

---

## positions

Purpose:

Operational Source Of Truth.

Owns:

* entry_price
* current_price
* unrealized_pnl
* realized_pnl
* position_size
* status
* updated_at

---

## portfolio_state

Purpose:

Derived operational snapshot.

Must never become the primary source of truth.

---

## paper_portfolio

Purpose:

Historical snapshots.

---

## executions

Purpose:

Immutable history.

Audit trail.

Research dataset.

Not operational truth.

---

# KNOWN ARCHITECTURAL DECISIONS

Confirmed:

## positions

Single Source Of Truth

## portfolio_state

Derived State

## executions

Immutable History

## Opportunity Centric Architecture

Target Model

## Exchange Agnostic

Required Future State

## Strategy Agnostic

Required Future State

---

# CURRENT PRIORITIES

Governed by:

DEPLOYMENT_CONTRACT.md

Current deployment items:

1. positions Source of Truth

2. portfolio_state snapshot

3. duplicate prevention

4. stop loss support

5. realized PnL on close

6. kill switch validation

No additional scope.

---

# DO NOT RECOMMEND

Do not recommend:

* complete rewrites
* rebuilding the project from scratch
* lifecycle engines
* outcome engines
* economic memory
* meta intelligence expansion
* new agents
* additional domains
* "while we're here"

Infrastructure comes first.

Discovery is not authorization.

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

1. DEPLOYMENT_CONTRACT.md
2. PROJECT_STATUS.md
3. NEXT_SESSION.md
4. MORPHO_BOOTSTRAP.md

Read them completely before making architectural recommendations.

---

# DOCUMENT HIERARCHY

Morpho documentation is intentionally separated into layers.

The objective is operational clarity, not documentation overload.

---

# TIER 1 — CORE OPERATIONAL DOCUMENTS

## DEPLOYMENT_CONTRACT.md

Purpose:

Scope authority.

Answers:

"What is allowed?"

---

## NEXT_SESSION.md

Purpose:

Immediate objective.

Answers:

"What are we doing now?"

---

## PROJECT_STATUS.md

Purpose:

Current operational reality.

Answers:

"What is the real state of the system?"

---

## MORPHO_BOOTSTRAP.md

Purpose:

Identity, philosophy and workflow.

Answers:

"What is Morpho and how should we approach it?"

---

# TIER 2 — ARCHITECTURE DOCUMENTS

Read only when working on architecture or operational design.

## MORPHO_OPERATIONAL_MODEL.md

Purpose:

High-level operational architecture map.

Defines:

* operational domains
* state hierarchy
* governance flow

---

## ARCHITECTURE_PRINCIPLES.md

Purpose:

Architectural doctrine.

Defines:

* ownership philosophy
* migration philosophy
* governance philosophy
* state separation rules

---

## DOMAIN ARCHITECTURE DOCUMENTS

Examples:

* PORTFOLIO_HEALTH_ARCHITECTURE.md
* RISK_STATE_ARCHITECTURE.md

Read only when working on those domains.

---

# TIER 3 — OPERATIONAL MEMORY

Historical reference.

These are NOT required reading during normal sessions.

## CHANGELOG.md

Tracks major changes.

## DECISION_LOG.md

Tracks important architectural decisions.

## INCIDENT_LOG.md

Tracks operational failures and lessons learned.

## RUNBOOK.md

Operational procedures and recovery instructions.

---

# RECOMMENDED SESSION WORKFLOW

Normal implementation session:

1. Read DEPLOYMENT_CONTRACT.md
2. Read PROJECT_STATUS.md
3. Read NEXT_SESSION.md

Read additional documents only when required.

Minimize cognitive overload.

Preserve continuity.

---

# CORE PRINCIPLES

Single owner per state.

Derived states adapt to Source of Truth maturity.

Reality ownership ≠ transition governance.

Infrastructure before intelligence.

Operational simplicity over sophistication.

Discovery is not authorization.

Reality over principles.

No principle is above reality.

Finite audits.

Infinite learning.

