# ARCHITECTURE INDEX — MORPHO AGENTS

## PURPOSE

This document provides a navigational map of Morpho Agents architecture and operational documentation.

Its purpose is to:

* accelerate onboarding
* preserve architectural continuity
* improve navigability
* reduce architectural drift
* guide future AI sessions
* organize operational knowledge

---

# CORE IDENTITY DOCUMENTS
## MORPHO_ACADEMY_RESEARCH_EXPANSION.md

Purpose:

Defines Morpho Academy evolution into a Strategic Intelligence & Ecosystem Understanding Layer.

Defines:

* research philosophy
* comparative systems analysis
* protocol intelligence
* opportunity structure analysis
* incident studies
* governance-oriented research
* complexity budget discipline
* survivability analysis
* evolutionary judgment development

Purpose:

Preserve strategic cognition, ecosystem understanding, and governance-oriented research discipline while Morpho evolves.
## MORPHO_VISION.md

Purpose:

High-level strategic vision document.

Defines:

* long-term vision
* opportunity-centric philosophy
* future strategic direction
* external narrative / pitch direction

Important:

This document does NOT guide implementation decisions.

---

## MORPHO_BOOTSTRAP.md

Purpose:

Rapid project context transfer.

Defines:

* project identity
* core thesis
* current project phase
* architectural priorities
* development philosophy
* operational protocol

Recommended first-read document for new sessions.

---

## PROJECT_STATUS.md

Purpose:

Primary operational architecture status document.

Defines:

* current architecture
* current phase
* audits completed
* architectural gaps
* roadmap
* ownership direction
* operational priorities

Primary operational source for implementation direction.

---

# CORE ARCHITECTURE DOCUMENTS

## MORPHO_OPERATIONAL_MODEL.md

Purpose:

High-level operational architecture model.

Defines:

* operational domains
* state hierarchy
* governance flow
* derived operational intelligence
* Source Of Truth relationships
* operational coordination model

Recommended architectural overview document.

---

## ARCHITECTURE_PRINCIPLES.md

Purpose:

Architectural doctrine and principles.

Defines:

* ownership philosophy
* governance philosophy
* migration philosophy
* operational architecture doctrine
* state separation principles
* centralized governance principles

Guides architectural decisions.

---
## GOVERNANCE_EVOLUTION_PRINCIPLES.md

Purpose:

Long-term governance evolution doctrine and expansion discipline framework.

Defines:

* governability-first evolution
* capability expansion constraints
* connector isolation philosophy
* infrastructure identity preservation
* complexity budget discipline
* governance anti-patterns
* operational expansion checklists
* evolutionary risk management

Purpose:

Prevent architectural drift and preserve operational coherence during future expansion.
# DOMAIN ARCHITECTURE DOCUMENTS
## POSITION_STATE_ARCHITECTURE.md

Purpose:

Defines the future canonical live economic Source Of Truth for Morpho.

Defines:

* live position semantics
* exposure semantics
* mark-to-market foundations
* unrealized pnl foundations
* reconciliation foundations
* governance visibility
* economic truthfulness

Important distinction:

Separates:

* historical execution memory

from:

* live deployed capital state

Purpose:

Establish future economic reality semantics and canonical position governance architecture.
## PORTFOLIO_HEALTH_ARCHITECTURE.md

Purpose:

Defines Portfolio Health domain architecture.

Defines:

* structural fragility philosophy
* portfolio operational health
* governance escalation relationship
* portfolio domain boundaries
* operational responsibilities

---

## PORTFOLIO_HEALTH_STATE_SCHEMA.md

Purpose:

Defines operational schema for:

portfolio_health_state.json

Defines:

* operational structure
* metrics
* governance recommendation format
* threshold philosophy
* schema versioning
* machine-readable operational intelligence

---

## RISK_STATE_ARCHITECTURE.md

Purpose:

Defines Risk State domain architecture.

Defines:

* environmental operational danger
* telemetry-driven risk assessment
* governance recommendation flow
* environmental vs structural separation
* risk domain boundaries

---

# OPERATIONAL MEMORY DOCUMENTS

## DECISION_LOG.md

Purpose:

Records important architectural and operational decisions.

Includes:

* decision rationale
* tradeoffs
* alternatives considered
* consequences

Purpose:

Preserve institutional memory.

---

## INCIDENT_LOG.md

Purpose:

Records operational incidents and failures.

Includes:

* incident description
* impact
* root cause
* resolution
* prevention strategy

Purpose:

Improve operational resilience over time.

---

## CHANGELOG.md

Purpose:

Tracks project evolution and major changes.

Includes:

* features added
* architecture changes
* migrations
* operational improvements

Purpose:

Provide historical operational traceability.

---

## RUNBOOK.md

Purpose:

Operational procedures and recovery actions.

Includes:

* restart procedures
* kill switch operations
* operational recovery
* deployment procedures
* troubleshooting

Purpose:

Operational continuity and recovery support.

---

# SESSION CONTINUITY DOCUMENTS

## NEXT_SESSION.md

Purpose:

Session continuity and short-term operational planning.

Defines:

* next priorities
* pending architectural questions
* current implementation focus
* active migration direction

Must be updated at the end of sessions.

---

# SOURCE OF TRUTH HIERARCHY

## position_state

Operational Source Of Truth.

Current Owner:

position_manager.py

Future Owner:

Position Engine

---

## runtime_state.json

Runtime operational state.

Owner:

runtime_monitor.py

---

## kill_switch_state.json

Governance operational state.

Owner:

kill_switch_manager.py

---

## portfolio_health_state.json (future)

Derived structural operational intelligence.

Owner:

portfolio_health_manager.py

---

## risk_state.json (future)

Derived environmental operational intelligence.

Owner:

risk_state_manager.py

---

# OPERATIONAL DOMAIN MODEL

Morpho currently defines four primary operational domains.

---

## Runtime State

Question:

"Is the machine operational?"

---

## Portfolio Health

Question:

"Is deployed capital structurally healthy?"

---

## Risk State

Question:

"How dangerous is the current operational environment?"

---

## Governance

Question:

"What operational actions are allowed?"

---

# OPERATIONAL FLOW MODEL

Source Of Truth
↓
Manager
↓
Derived Operational State
↓
Governance Recommendation
↓
Centralized Enforcement

---

# GOVERNANCE MODEL

Governance remains centralized through:

kill_switch_manager.py

Operational domains:

* evaluate
* score
* escalate
* recommend

Governance:

* decides
* persists
* enforces

safe_runner.py represents the primary enforcement layer.

---

# DEVELOPMENT PHILOSOPHY

Morpho prioritizes:

Architecture

>

Features

Observability

>

Optimization

Incremental Migration

>

Big Bang Refactors

Operational Clarity

>

Premature Intelligence

Durability

>

Speed

---

# RECOMMENDED READING ORDER

For new AI sessions or collaborators:

1. MORPHO_BOOTSTRAP.md
2. PROJECT_STATUS.md
3. NEXT_SESSION.md
4. MORPHO_OPERATIONAL_MODEL.md
5. ARCHITECTURE_PRINCIPLES.md

Then:

* domain architecture documents
* operational memory documents
* implementation-specific files

---

# CURRENT FOUNDATION DIRECTION

Morpho is evolving toward:

Autonomous Operational Infrastructure for Digital Capital.

The long-term objective is not merely trading automation.

The objective is coordinated operational intelligence capable of:

* opportunity evaluation
* structural fragility assessment
* environmental danger assessment
* governance coordination
* operational resilience
* autonomous infrastructure evolution

