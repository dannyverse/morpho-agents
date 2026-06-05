# ARCHITECTURE PRINCIPLES — MORPHO AGENTS

## PURPOSE

This document records the architectural principles that have emerged through:

* implementation
* audits
* operational incidents
* multi-LLM architectural review
* iterative refinement

These principles should guide future architectural decisions.

This document is not a roadmap.

This document defines architectural doctrine.

---

# ARCHITECTURAL CONSENSUS

After contrasting the architecture with multiple LLM reviews (Claude + Grok), the following principles are now considered strongly validated.

---

## CONFIRMED ARCHITECTURAL PRINCIPLES

### Live State vs Historical Logs

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

### Ownership Boundaries

Ownership boundaries are critical.

Each operational domain should have:

* one owner
* one authoritative state
* one responsibility boundary

---

### Governance Persistence

Governance state must persist independently from runtime memory.

Governance is not a temporary runtime condition.

Governance is operational state.

---

### Runtime Self-Protection

Runtime self-protection is now part of Morpho core architecture.

The system must be capable of:

* detecting unsafe conditions
* persisting governance state
* halting execution safely
* recovering safely

without manual operational intervention.

---

### Incremental Migration Philosophy

Incremental migration is preferred over big-bang refactors.

Migration pattern:

1. Create specialized states/tables
2. Dual writes during transition
3. Migrate consumers incrementally
4. Deprecate legacy structures after validation

Large simultaneous refactors increase operational risk.

---

### StateManager Direction

StateManager should evolve toward:

* centralized read abstraction
* validated write gateway
* unified operational access layer

Direct JSON access from modules should gradually disappear over time.

---

# CONFIRMED OWNERSHIP DIRECTION

## runtime_monitor.py

Role:

sole runtime state owner

---

## kill_switch_manager.py

Role:

sole governance state owner

---

## future portfolio_health_manager.py

Role:

portfolio health owner

---

## future risk_state_manager.py

Role:

risk state owner

---

# EMERGING ARCHITECTURAL DIRECTION

Morpho is transitioning from:

loosely connected scripts

toward:

* coordinated operational infrastructure
* governance-aware runtime architecture
* autonomous operational system foundation

---

# REMAINING ARCHITECTURAL QUESTIONS

Portfolio Health Architecture has now been formalized in:

PORTFOLIO_HEALTH_ARCHITECTURE.md

The following questions remain unresolved and should guide future Foundation sessions.

---

## position_state ↔ portfolio_state circularity

Status:

HIGH PRIORITY

---

## portfolio_health_state responsibilities

Questions:

* What is portfolio health?
* What belongs in portfolio_health_state?
* Should portfolio health trigger governance actions?

---

## risk_state decomposition boundaries

Questions:

* What belongs in risk_state?
* What belongs in runtime_state?
* What belongs in portfolio_health_state?

---

## exchange abstraction architecture

Status:

NOT IMPLEMENTED

Future requirement:

exchange-agnostic opportunity execution layer

---

## governance trigger interfaces

Operational domains should not manipulate runtime behavior directly.

Governance ownership should remain centralized through:

kill_switch_manager.py

Potential pattern:

portfolio_health_manager.py
↓
kill_switch_manager.activate_kill_switch()
↓
governance persistence
↓
safe_runner enforcement

# RELATED ARCHITECTURE DOCUMENTS

The following architectural domains have now been formalized:

* PORTFOLIO_HEALTH_ARCHITECTURE.md
* PORTFOLIO_HEALTH_STATE_SCHEMA.md

These documents define:

* Portfolio Health responsibilities
* operational boundaries
* governance interfaces
* state structure
* structural fragility philosophy
* operational schema design

# FORMALIZED OPERATIONAL DOMAINS

The following operational domains have now been formally defined:

* Runtime State
* Portfolio Health
* Risk State
* Governance State

Related architecture documents:

* PORTFOLIO_HEALTH_ARCHITECTURE.md
* PORTFOLIO_HEALTH_STATE_SCHEMA.md
* RISK_STATE_ARCHITECTURE.md

These domains establish:

* operational ownership boundaries
* governance escalation patterns
* derived operational intelligence states
* environmental vs structural separation
* centralized governance enforcement

