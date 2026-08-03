# INCIDENT LOG — MORPHO AGENTS

## PURPOSE

This document records significant operational, architectural and governance incidents.

The objective is not blame.

The objective is institutional learning.

Each incident should answer:

* What happened?
* Why did it happen?
* How was it resolved?
* How can it be prevented in the future?

---

# INCIDENT 001

## Historical Position Explosion

Date:

May 2026

Severity:

HIGH

Status:

RESOLVED

---

### Description

The system unexpectedly accumulated approximately 26,000 positions.

Portfolio metrics became unreliable.

Operational state became contaminated by historical data.

---

### Root Cause

Position-related modules were reading historical records as if they were active operational state.

The architecture lacked clear separation between:

* operational state
* historical state

Cycle awareness was missing.

Historical executions were incorrectly influencing live system behavior.

---

### Impact

* Position counts became invalid
* Portfolio metrics became distorted
* Risk calculations became unreliable
* Operational state lost integrity

---

### Resolution

Implemented:

* Source Of Truth Audit
* Executions Dependency Audit
* Flow Of State Audit
* Position Ownership Audit

Confirmed:

position_state

as the single operational Source Of Truth.

Introduced:

cycle_id architecture

to separate historical execution data from current operational state.

---

### Prevention

Maintain strict separation between:

* Live Operational State
* Historical Records

All future operational queries must remain cycle-aware.

Historical tables must never become operational dependencies.

---

### Lessons Learned

Source of Truth must be explicitly defined.

Historical data should support analysis, not operational decisions.

Architectural ambiguity creates hidden systemic risk.

---

# INCIDENT 002

## Governance State Fragmentation

Date:

June 2026

Severity:

MEDIUM

Status:

RESOLVED

---

### Description

Two governance mechanisms existed simultaneously:

* HALT_TRADING.txt
* kill_switch_state.json

This created duplicated responsibility and fragmented governance ownership.

---

### Root Cause

Legacy governance controls remained active while the new governance architecture was being introduced.

Ownership had not yet been consolidated.

---

### Impact

Governance state existed in multiple locations.

Potential future inconsistencies could occur between runtime enforcement and governance state.

---

### Resolution

Introduced:

kill_switch_manager.py

as governance owner.

Integrated:

risk_manager.py
→ kill_switch_manager.py

while maintaining temporary backward compatibility.

Adopted incremental migration strategy.

---

### Prevention

Each operational domain must have:

* one owner
* one state
* one authoritative source

---

### Lessons Learned

Governance requires ownership.

Migration should occur gradually through validation and dual-write phases.

Big-bang governance refactors increase operational risk.

============================================================
INCIDENT ID: 2026-06-25-001
============================================================

Title

Unsupervised Runtime Termination

------------------------------------------------------------

Severity

HIGH

------------------------------------------------------------

Summary

Morpho ceased execution during unattended operation.

No operating system failures were detected.

No application crash evidence was found.

The runtime had been executed as an unsupervised long-running process.

------------------------------------------------------------

Root Cause

Absence of a production supervision layer.

The supervisor process ceased execution without observable termination signals or logging instrumentation.

This incident does not indicate functional instability of the trading system.

It revealed a production infrastructure gap.

------------------------------------------------------------

Evidence

Confirmed:

✓ No OOM
✓ No kernel panic
✓ No segmentation fault
✓ No reboot
✓ No Kill Switch activation
✓ Trading logic operational

------------------------------------------------------------

Corrective Actions

Implemented:

✓ systemd service

✓ Restart=always

✓ Persistent journald logging

✓ Runtime executed through project virtual environment

✓ SQLite compatibility fixes

✓ Execution schema alignment

------------------------------------------------------------

Validation

Runtime successfully validated.

15 / 15 modules operational.

Runtime Status:

HEALTHY

Safe Runner Exit Code:

0

------------------------------------------------------------

Follow-up

Production Burn-in Period initiated.

Daily verification:

- systemctl status morpho.service

- systemctl show morpho.service -p NRestarts

- journalctl -u morpho.service

Duration:

Approximately 10 days.

------------------------------------------------------------

Status

CLOSED

---

# INCIDENT: Portfolio State Stale Snapshot

Fecha:
31 Julio 2026

Severity:
LOW / MEDIUM

## Descripción

Durante una auditoría de coherencia de estados se detectó una discrepancia entre el estado derivado interno de Morpho y la realidad del exchange.

Risk Manager mostraba:

Open Positions: 2

Mientras Hyperliquid mostraba:

Open Positions: 0
Open Orders: 0

---

## Evidencia recopilada

### Hyperliquid

Resultado:

- Account Value: 0.0
- Open Positions: 0
- Open Orders: 0

### Reconciliación

Script:

audit_position_reconciliation.py

Resultado:

POSITIONS MISSING IN SQLITE

Sin registros.

No existían posiciones reales en exchange ausentes en SQLite.

### Estado interno

portfolio_state contenía:

- CASHCAT SHORT OPEN
- HMSTR LONG OPEN

Timestamp:

2026-07-30 21:12:06

---

## Investigación

La cadena encontrada:

positions
    |
    v
portfolio_state
    |
    v
risk_manager


risk_manager no consulta directamente Hyperliquid.

Lee:

SELECT *
FROM portfolio_state
WHERE status='OPEN'


portfolio_state.py genera el snapshot desde:

SELECT *
FROM positions
WHERE status='OPEN'


---

## Root Cause

El problema no estaba en ejecución ni en exposición real.

Era un snapshot derivado persistente desactualizado en portfolio_state.

La regeneración manual mediante:

python portfolio_state.py

eliminó la discrepancia.

Resultado:

portfolio_state quedó vacío porque positions no tenía posiciones abiertas.

---

## Impacto

NO afectó:

- fondos reales
- posiciones reales en Hyperliquid
- ejecución live

Impacto:

Risk Manager podía interpretar temporalmente posiciones internas antiguas.

---

## Acción futura

Evaluar:

- validación de freshness de portfolio_state
- reconciliación bidireccional Exchange ↔ Internal State
- evitar que estados derivados antiguos influyan en decisiones críticas

---

## Estado

Cerrado como investigación.

No requiere cambio inmediato de arquitectura.

Pendiente observar si vuelve a reproducirse durante operación normal.


---

# INVESTIGATION — Live Execution Authority Validation

## Date

2026-08-03

## Observation

During runtime observation, no new live executions were occurring despite the presence of market opportunities.

## Investigation

Validated the complete execution pipeline:

- Signal generation: ACTIVE
- Opportunity scoring: ACTIVE
- Confidence evaluation: ACTIVE
- Execution decision: BLOCKED BY AUTHORITY

Example validated opportunity:

Asset: KAITO

Direction: SHORT

Score: 4.9

Confidence: 81.44

Rationale:

persistent funding anomaly

Execution result:

Status: REJECTED

Reason:

LIVE_EXECUTION_NOT_AUTHORIZED

Action:

BLOCKED

## Root Cause

No issue detected in signal generation, scoring, or confidence calculation.

Live execution remains disabled by design through:

execution_authority.py

Configuration:

LIVE_EXECUTION_AUTHORIZED = False

## Conclusion

Morpho is detecting valid opportunities and reaching the execution authorization layer correctly.

Current operational state:

Opportunity detection: ACTIVE

Signal evaluation: ACTIVE

Risk evaluation: ACTIVE

Live execution: BLOCKED BY GOVERNANCE

No code change required.
