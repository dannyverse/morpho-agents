# MORPHO OPERATIONAL MODEL

## PURPOSE

This document describes the operational architecture model of Morpho Agents.

Its objective is to explain:

* operational domains
* ownership boundaries
* Source Of Truth hierarchy
* state relationships
* governance flow
* operational intelligence layers
* enforcement flow

This document represents the current operational architecture direction of Morpho during Foundation Phase.

---

# CORE ARCHITECTURAL MODEL

Morpho is transitioning from:

loosely connected scripts

toward:

state-driven operational infrastructure.

The system is organized around:

* operational domains
* explicit ownership
* derived operational intelligence
* centralized governance
* autonomous runtime coordination

---

# SOURCE OF TRUTH HIERARCHY

## position_state

Role:

Operational Source Of Truth for deployed capital.

Purpose:

* active positions
* deployed exposure
* operational portfolio state

Current Technical Owner:

position_manager.py

Future Architectural Owner:

Position Engine

---

## executions

Role:

Immutable historical execution history.

Purpose:

* audit trail
* analytics
* research
* telemetry

NOT operational state.

NOT operational dependency.

---

## portfolio_state

Role:

Derived operational representation.

Status:

Active but still partially circular.

Known architectural issue:

position_state
↔
portfolio_state

Circularity remains unresolved.

---

# OPERATIONAL DOMAINS

Morpho currently defines four primary operational domains.

---

# 1. Runtime State

Question:

"Is the machine operational?"

Owner:

runtime_monitor.py

Operational State:

runtime_state.json

Responsibilities:

* runtime coordination
* runtime flags
* system operational status
* execution cycle monitoring

---

# 2. Portfolio Health

Question:

"Is deployed capital structurally healthy?"

Owner:

portfolio_health_manager.py

Future Operational State:

portfolio_health_state.json

Responsibilities:

* structural fragility assessment
* concentration analysis
* deployment quality analysis
* capital structure evaluation
* operational health scoring

Portfolio Health evaluates internal structural quality of deployed capital.

---

# 3. Risk State

Question:

"How dangerous is the current operational environment?"

Owner:

risk_state_manager.py

Future Operational State:

risk_state.json

Responsibilities:

* market danger assessment
* infrastructure instability assessment
* liquidity deterioration detection
* exchange instability monitoring
* environmental operational risk analysis

Risk State evaluates external/environmental danger.

---

# 4. Governance State

Question:

"What operational actions are allowed?"

Owner:

kill_switch_manager.py

Operational State:

kill_switch_state.json

Responsibilities:

* kill switch persistence
* governance enforcement
* operational protection
* execution permission control

Governance remains centralized.

---

# DOMAIN SEPARATION

## Runtime State

Evaluates:

machine operational integrity.

---

## Portfolio Health

Evaluates:

internal structural fragility of deployed capital.

---

## Risk State

Evaluates:

external environmental operational danger.

---

## Governance

Controls:

operational permissions and enforcement.

---

# DERIVED OPERATIONAL INTELLIGENCE

Morpho is evolving toward a layered architecture:

Source Of Truth
↓
Manager
↓
Derived Operational State
↓
Governance Recommendation
↓
Centralized Enforcement

Examples:

position_state
↓
portfolio_health_manager.py
↓
portfolio_health_state.json

---

telemetry
↓
risk_state_manager.py
↓
risk_state.json

---

runtime telemetry
↓
runtime_monitor.py
↓
runtime_state.json

---

# GOVERNANCE FLOW

Operational domains should NOT directly manipulate runtime execution.

Operational domains may:

* evaluate
* score
* escalate
* recommend governance action

Governance decides enforcement.

Operational flow:

operational state / telemetry
↓
domain manager
↓
derived operational state
↓
governance recommendation
↓
kill_switch_manager.py
↓
safe_runner.py

---

# CENTRALIZED ENFORCEMENT MODEL

safe_runner.py represents the primary operational enforcement layer.

Execution may be halted when:

kill_switch_active = true

Governance persistence survives:

* crashes
* restarts
* runtime failures

This behavior is now considered foundational architecture.

---

# STATE MANAGER DIRECTION

StateManager is evolving toward:

* centralized read abstraction
* validated write gateway
* unified operational access layer

Future direction:

Direct JSON access should gradually disappear from modules.

---

# ARCHITECTURAL PRINCIPLES

Morpho architectural direction prioritizes:

* ownership clarity
* operational observability
* governance centralization
* incremental migration
* state-driven coordination
* operational resilience
* explainable operational intelligence

---

# PHASE 0 OBJECTIVE

Foundation Phase objective is NOT advanced intelligence.

Foundation objective is:

* stable operational architecture
* clean ownership boundaries
* governance safety
* operational visibility
* structural observability
* runtime resilience

---

# CURRENT EMERGING MODEL

Morpho is evolving toward:

Autonomous Operational Infrastructure for Digital Capital.

The objective is not merely strategy execution.

The objective is coordinated operational intelligence capable of:

* evaluating opportunities
* evaluating structural fragility
* evaluating environmental danger
* coordinating governance
* protecting deployed capital
* evolving operational capability over time

