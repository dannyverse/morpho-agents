# MORPHO AGENTS — DECISION LOG

This document records major architectural and operational decisions taken during Morpho development.

Its purpose is to preserve:

* architectural reasoning
* tradeoffs considered
* implementation motivations
* known consequences
* and historical context behind important changes.

This document complements:

* `PROJECT_STATUS.md`
* `OBSERVABILITY_ARCHITECTURE.md`
* `NEXT_SESSION.md`

by explaining WHY decisions were made, not only WHAT was implemented.

---

# 2026-05-29 — position_state as operational source of truth

## Decision

Use `position_state` as primary operational state source instead of reconstructing state from historical execution logs.

## Reasoning

Historical executions caused:

* duplicated positions
* historical contamination
* incorrect live exposure calculations
* operational inconsistency

Operational systems require:

* isolated live state
* cycle-aware execution
* explicit operational ownership

## Consequences

Introduced need for:

* cycle_id architecture
* state isolation
* operational vs historical separation

## Known Follow-Ups

* gradual system_log decomposition
* centralized state access
* stronger ownership boundaries

---

# 2026-06-03 — Runtime Observability Architecture

## Decision

Separate:

* live operational state
* from historical telemetry/logging

## Reasoning

`system_log` had become overloaded with:

* runtime state
* portfolio telemetry
* risk information
* historical analytics

This created unclear ownership and architectural coupling.

## Result

Introduced:

* `runtime_monitor.py`
* `runtime_state.json`
* atomic state persistence
* runtime ownership model

## Consequences

Established:

* live state architecture
* operational heartbeat persistence
* centralized runtime truth

---

# 2026-06-03 — StateManager Introduction

## Decision

Introduce `state_manager.py` as centralized operational state access layer.

## Reasoning

Direct JSON access from multiple modules creates:

* coupling
* inconsistent reads
* future migration difficulty

A centralized access layer improves:

* ownership clarity
* backend abstraction
* future scalability

## Long-Term Direction

StateManager is expected to evolve toward:

* centralized read abstraction
* validated write gateway
* unified operational state layer

---

# 2026-06-03 — Kill Switch Governance Persistence

## Decision

Persist governance state in:
`kill_switch_state.json`

instead of keeping governance only in runtime memory.

## Reasoning

Governance state must survive:

* crashes
* restarts
* execution interruptions

Persistent governance state improves:

* operational safety
* coordination
* runtime self-protection

## Result

Introduced:

* `kill_switch_manager.py`
* governance persistence
* runtime enforcement loop

---

# 2026-06-03 — Autonomous Governance Enforcement

## Decision

`safe_runner.py` must check kill switch state before execution.

## Reasoning

Risk governance must have authority over execution runtime.

Detection without enforcement creates false safety.

## Result

Implemented:

* governance enforcement loop
* execution abort behavior
* runtime self-protection

## Architectural Importance

This marks the transition from:

* isolated scripts

toward:

* coordinated operational infrastructure

---

# 2026-06-03 — Vision / Architecture Separation

## Decision

Separate:

* long-term project vision
* from operational architecture documents

## Reasoning

Strategic concepts such as:

* Strategy Factory
* Institutional Memory
* Adaptive Edge Evolution

represent long-term direction, not immediate implementation priorities.

Operational documents must remain:

* precise
* executable
* implementation-oriented

## Result

Created:

* `MORPHO_VISION.md`

while preserving:

* `PROJECT_STATUS.md`
* `OBSERVABILITY_ARCHITECTURE.md`
* `NEXT_SESSION.md`

as operational architecture documents.

---

## June 2026 — Risk Manager Consumer Alignment

### Context

`position_state` schema was recently expanded with:

* `position_type`
* `status`
* `opened_at`

`risk_manager.py` still referenced legacy directional fields:

```python id="x2c3qv"
direction == "LONG"
direction == "SHORT"
```

which no longer matched the operational schema.

---

### Decision

`risk_manager.py` now consumes:

```text id="n8m4ld"
position_state
```

instead of:

```text id="g6j1zk"
portfolio_state
```

for directional exposure calculations.

---

### Reasoning

At the current Foundation stage:

* `position_state` is the most complete operational Source of Truth
* it contains the granular position metadata required by risk evaluation
* `portfolio_state` still appears partially aggregated / incomplete

This change restores:

* schema alignment
* directional calculations
* consumer consistency

while preserving:

* runtime simplicity
* operational clarity
* incremental migration philosophy

---

### Important Note

This decision may evolve later.

Future architecture may:

* redefine ownership boundaries
* consolidate portfolio aggregation
* introduce richer exposure models

For now, this change is considered:

* operationally correct
* minimally invasive
* Foundation-aligned

---

---

## June 2026 — Direction vs Position Type Clarification

### Context

Initial schema migration work suggested that:

```text id="a8m2qp"
direction
```

was a legacy field that should be fully replaced by:

```text id="b4n7zk"
position_type
```

However, a grep-based architectural audit revealed that:

* `direction`
* `LONG`
* `SHORT`

remain operationally active across multiple upstream layers:

* `execution_agent.py`
* `portfolio_state.py`
* `signal_memory.py`
* `paper_trading_engine.py`
* `portfolio_dashboard.py`

---

### Important Discovery

The issue was NOT that:

```text id="c9x5rv"
direction
```

was obsolete.

The real issue was:

```text id="d3m8ld"
position_state
```

was introduced with a partially transitional schema
that is not yet fully integrated with the upstream directional flow.

---

### Current Interpretation

At the current Foundation stage:

| Concept         | Status                                           |
| --------------- | ------------------------------------------------ |
| `direction`     | operationally active upstream                    |
| `position_type` | transitional placeholder inside `position_state` |
| migration       | incomplete by design                             |
| ownership       | still evolving                                   |

---

### Important Principle

Future migrations should avoid assuming that:

* schema divergence
  automatically means:
* legacy obsolescence.

Operational grep audits and runtime validation are required before performing semantic migrations.

---

### Temporary Foundation-State Decision

`position_type` remains temporarily hardcoded as:

```python id="f7v1nm"
"LONG"
```

inside:

```text id="g2k4pr"
position_manager.py
```

until:

* execution semantics
* opportunity taxonomy
* strategy ownership

become more formally defined.

This is considered:

* explicit
* controlled
* non-dangerous technical debt.

---

