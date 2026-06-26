## v0.4.0 — June 2026

### Added

* kill_switch_manager.py
* Persistent governance state (kill_switch_state.json)
* Governance recovery flow
* INCIDENT_LOG.md

### Changed

* risk_manager.py integrated with kill_switch_manager
* safe_runner.py now participates in governance lifecycle
* Governance architecture moved toward centralized ownership

### Architectural Impact

* Governance lifecycle completed:

  * Detect
  * Activate
  * Persist
  * Enforce
  * Recover

* Dual-write migration initiated:

  * HALT_TRADING.txt
  * kill_switch_state.json

* Governance ownership formalized through kill_switch_manager.py



# MORPHO AGENTS — CHANGELOG

All notable operational and architectural changes to Morpho are documented here.

The purpose of this document is to maintain:

* release history
* architectural evolution tracking
* deployment visibility
* operational traceability

Format inspired by:
Keep a Changelog

---

# v0.4.0 — 2026-06-03

## Added

* `runtime_monitor.py`
* `runtime_state.json`
* atomic runtime state persistence
* `state_manager.py`
* `kill_switch_manager.py`
* `kill_switch_state.json`
* governance enforcement loop
* `MORPHO_VISION.md`
* `DECISION_LOG.md`

## Changed

* `safe_runner.py`

  * runtime state integration
  * kill switch enforcement

* `logger.py`

  * migrated to StateManager runtime access

* `risk_manager.py`

  * runtime awareness added
  * StateManager integration

## Architectural Improvements

* Live State vs Historical Logs separation
* centralized runtime ownership
* governance persistence
* runtime self-protection
* operational architecture clarification
* vision vs implementation separation

---

# v0.3.0 — 2026-05-31

## Added

* cycle_id architecture
* operational state isolation
* governance groundwork
* runtime coordination improvements

## Changed

* position handling logic
* operational state queries
* exposure calculations

## Fixed

* historical execution contamination
* duplicated operational positions
* runaway position growth issue

---

# v0.2.0 — 2026-05-29

## Added

* foundational multi-agent orchestration
* portfolio coordination systems
* risk management layer
* signal memory architecture
* adaptive scoring foundation

## Changed

* portfolio state handling
* execution coordination
* historical tracking structure

---

# v0.1.0 — Initial Foundation

## Added

* early multi-agent trading infrastructure
* signal generation agents
* paper trading foundation
* portfolio management systems
* SQLite operational database
* basic orchestration runtime

============================================================
2026-06-26
Production Hardening Session
============================================================

Added

- Migrated runtime supervision from tmux to systemd.
- Enabled automatic service restart.
- Enabled persistent journald logging.
- Standardized runtime on project virtual environment.
- Updated safe_runner to execute modules using the project Python interpreter.
- Migrated signal_analytics.py from legacy CSV to SQLite.
- Migrated adaptive_scoring.py from legacy CSV to SQLite.
- Extended executions schema with:
  - entry_price
  - position_size
  - cycle_id

Fixed

- Resolved "python: not found" failures under systemd.
- Resolved execution persistence schema mismatch.
- Eliminated legacy CSV dependency for signal analytics.
- Restored full runtime execution.

Validation

- Runtime supervision operational.
- 15/15 modules completed successfully.
- Safe Runner Exit Code = 0.
- Runtime Status = HEALTHY.
- Production Burn-in Period initiated.
