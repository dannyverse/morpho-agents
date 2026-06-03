# MORPHO OBSERVABILITY ARCHITECTURE

## STATUS

Phase 0 Foundation Architecture

June 2026

---

# PURPOSE

This document formalizes Morpho’s initial Observability Architecture.

The objective is to define:

* operational observability layers
* ownership boundaries
* live state vs historical telemetry
* runtime health modeling
* migration principles
* implementation scope

before major observability refactors begin.

This is an architecture and implementation-guidance document.

Not a production implementation specification.

---

# CORE OBSERVABILITY PRINCIPLE

Observability is NOT logging.

Observability is the system’s capability to understand:

* operational runtime condition
* portfolio condition
* risk condition
* failures
* degradation
* runtime behavior
* system health

in real time.

---

# OBSERVABILITY PHILOSOPHY

Each operational layer must own its own observability.

Morpho should avoid:

* generic global logs
* mixed ownership
* multi-purpose telemetry tables
* operational ambiguity

Morpho should prefer:

* specialized observability layers
* explicit ownership
* live operational state
* clear telemetry separation
* incremental evolution

---

# LIVE STATE vs HISTORICAL LOGS

This is one of the most important architectural distinctions in Morpho.

---

## LIVE STATE

Represents:

```text
current operational condition
```

Examples:

* current runtime health
* current portfolio health
* current risk state

Properties:

* mutable
* current snapshot
* operationally critical
* low latency access
* consumed by runtime systems

Recommended storage:

```text
JSON live state files
```

---

## HISTORICAL LOGS

Represents:

```text
historical telemetry and events
```

Examples:

* runtime failures
* historical alerts
* historical drawdowns
* historical system degradation
* analytics telemetry

Properties:

* append-only
* historical
* analytics-oriented
* audit-oriented

Recommended storage:

```text
SQLite
```

---

# OBSERVABILITY LAYERS

---

# 1. RUNTIME OBSERVABILITY LAYER

## QUESTION ANSWERED

```text
Is the machine operational?
```

---

## ENTITY

```text
runtime_state
```

---

## TYPE

```text
Live Operational State
```

---

## RESPONSIBILITY

Represent the operational runtime condition of Morpho.

This layer measures:

* runtime health
* orchestration health
* heartbeat validity
* runtime degradation
* module failures

It does NOT measure:

* profitability
* strategy performance
* alpha generation

---

## OWNER

Current orchestration owner:

```text
safe_runner.py
```

Future dedicated runtime observability owner:

```text
runtime_monitor.py
```

---

## PROPOSED FIELDS

```text
cycle_id
heartbeat_timestamp
system_status
runtime_mode
active_modules
failed_modules
last_error
uptime_seconds
heartbeat_ok
cycle_duration_seconds
last_successful_cycle
```

Future optional fields:

```text
tokens_used_this_cycle
api_calls_this_cycle
memory_usage_mb
```

---

## SYSTEM STATUS STATES

Initial proposed states:

```text
INITIALIZING
HEALTHY
DEGRADED
RISK_MODE
HALTED
CRITICAL_FAILURE
```

---

## IMPORTANT PRINCIPLE

`system_status`

DOES NOT represent:

* PnL
* portfolio profitability
* strategy quality
* opportunity quality

It represents:

```text
runtime operational capability
```

---

## STORAGE

Live State:

```text
runtime_state.json
```

Historical Runtime Events:

```text
observability_events
```

(SQLite)

---

# 2. PORTFOLIO OBSERVABILITY LAYER

## QUESTION ANSWERED

```text
Is deployed capital operationally healthy?
```

---

## ENTITY

```text
portfolio_health_state
```

---

## TYPE

```text
Live Portfolio Telemetry
```

---

## RESPONSIBILITY

Represent the operational condition of deployed capital.

This layer measures:

* capital stability
* exposure condition
* drawdown condition
* portfolio operational stress

It does NOT measure:

* alpha quality
* strategy quality
* opportunity edge

---

## OWNER

Future logical owner:

```text
Portfolio Engine
```

Current distributed ownership across:

* portfolio_health.py
* related portfolio modules

---

## PROPOSED FIELDS

```text
equity
exposure
drawdown
open_positions
portfolio_health
```

Future optional fields:

```text
concentration_risk
liquidity_risk
```

---

## PORTFOLIO HEALTH STATES

Initial proposed states:

```text
HEALTHY
WARNING
UNSTABLE
CRITICAL
```

---

## STORAGE

Live State:

```text
portfolio_health_state.json
```

Historical Events:

```text
observability_events
```

(SQLite)

---

# 3. RISK OBSERVABILITY LAYER

## QUESTION ANSWERED

```text
Are current operating conditions acceptable?
```

---

## ENTITY

```text
risk_state
```

---

## TYPE

```text
Live Risk Telemetry
```

---

## RESPONSIBILITY

Represent operational and financial risk conditions affecting Morpho.

Risk is NOT defined only as losses.

Risk is defined as:

```text
Probability of unacceptable system damage.
```

This includes:

* capital risk
* market risk
* operational risk
* execution risk

---

## OWNER

Future logical owner:

```text
Risk Engine
```

Current probable owner:

```text
risk_manager.py
```

---

## PROPOSED FIELDS

```text
risk_status
kill_switch
max_drawdown_breached
exposure_limit_breached
volatility_regime
active_circuit_breakers
capital_restriction_level
daily_loss
```

---

## RISK STATUS STATES

Initial proposed states:

```text
NORMAL
DEFENSIVE
HIGH_RISK
CRITICAL
```

---

## IMPORTANT PRINCIPLE

`risk_status`

DOES NOT equal:

```text
system_status
```

Example:

```text
risk_status = HIGH_RISK
```

does NOT imply:

```text
system_status = CRITICAL_FAILURE
```

The runtime can remain operational while executing in defensive conditions.

---

## STORAGE

Live State:

```text
risk_state.json
```

Historical Events:

```text
observability_events
```

(SQLite)

---

# OBSERVABILITY ACCESS LAYER

Operational modules should NOT read JSON live states directly.

Morpho should evolve toward:

```text
StateManager
```

as the unified operational access layer.

Example:

```python
state = StateManager()

runtime = state.get_runtime_state()
portfolio = state.get_portfolio_health()
risk = state.get_risk_state()
```

This avoids:

* duplicated parsing
* inconsistent reads
* direct file coupling
* operational fragmentation

---

# ATOMIC STATE WRITES

All live state writes must be atomic.

Live operational JSON state files should never be written directly.

The system should use atomic replacement writes to avoid:

* partial writes
* corrupted runtime state
* concurrent write corruption
* inconsistent operational state

especially in future multi-agent or concurrent environments.

---

# PHASE 0 MINIMAL IMPLEMENTATION

Phase 0 implementation should remain intentionally simple.

The objective is:

* operational visibility
* reliability
* observability clarity
* stable ownership

NOT advanced telemetry complexity.

---

## INITIAL IMPLEMENTATION TARGET

Phase 0 recommended scope:

```text
runtime_state.json
portfolio_health_state.json
risk_state.json
observability_events
```

(SQLite)

---

## IMPORTANT PRINCIPLE

Phase 0 should prioritize:

```text
simple
stable
observable
incremental
```

over:

```text
premature complexity
over-engineering
large refactors
```

---

# SYSTEM_LOG DECOMPOSITION

Current implementation:

```text
system_log
```

mixes:

* runtime telemetry
* portfolio telemetry
* risk telemetry
* market regime information
* strategy analytics

This creates:

* ownership ambiguity
* mixed responsibilities
* unstable schema evolution
* operational confusion

---

# ARCHITECTURAL DECISION

`system_log`

should NOT remain the primary observability entity.

Morpho should evolve toward:

```text
specialized operational observability layers
```

with explicit ownership.

---

# MIGRATION STRATEGY

system_log decomposition must be incremental.

Recommended migration flow:

1. Create new specialized live states
2. Introduce dual writes during transition
3. Migrate readers progressively
4. Deprecate system_log only after validation

Big-bang replacements should be avoided.

---

# ALERTING PRINCIPLES

Initial recommended alert conditions:

```text
CRITICAL_FAILURE
kill_switch = True
```

→ immediate alert

---

```text
DEGRADED during multiple cycles
```

→ degradation alert

---

```text
drawdown thresholds exceeded
```

→ risk alert

---

# FUTURE OBSERVABILITY LAYERS

Not part of Phase 0 implementation.

---

## Opportunity Observability

Questions:

```text
Are opportunities still valid?
Is edge decaying?
Are opportunity models reliable?
```

Possible future fields:

```text
opportunity_score
validation_rate
edge_decay
opportunity_health
```

---

## Agent Observability

Questions:

```text
Are agents healthy?
Which agents degrade?
Which agents fail?
```

Possible future fields:

```text
agent_health
agent_accuracy
agent_failures
agent_latency
```

---

# IMPLEMENTATION ORDER

Recommended implementation sequence:

1. runtime_state.json
2. Runtime heartbeat
3. StateManager runtime access
4. portfolio_health_state.json
5. risk_state.json
6. observability_events
7. alerting integration
8. system_log decomposition
9. structured logging
10. advanced telemetry

---

# PHASE 0 OBJECTIVE

Phase 0 observability goal is NOT advanced monitoring sophistication.

The objective is:

```text
clear operational visibility
stable ownership
runtime reliability
clean telemetry separation
incremental architecture evolution
```

---

# CURRENT STATUS

Current status:

```text
ARCHITECTURE DESIGN PHASE
```

No major observability refactor should begin before architecture validation is complete.

