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

