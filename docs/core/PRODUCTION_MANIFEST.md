# MORPHO AGENTS — PRODUCTION MANIFEST

Version: 1.1

Status:
Operational Source of Truth

Purpose:

This document describes the current production environment.

Its objective is to eliminate uncertainty about operational reality.

If this document differs from production,
production is considered authoritative until the discrepancy is resolved.

---

# PRODUCTION ENVIRONMENT

Production Host:
morpho-node

VPS Provider:
Vultr

Operating System:
Ubuntu 24.04.4 LTS

Hostname:
morpho-node

IP Address:
140.82.57.36

Project Directory:
/root/morpho-agents

Python Version:
3.12.3

Virtual Environment:
/root/morpho-agents/venv

Deployment Date:
2026-06-26

Last Manifest Update:
2026-07-09

Production Operator:
Daniel

---

# DEPLOYED VERSION

Production Branch:
main

Production Commit:
1e45faba8e17acc985885771d610b1efe4f6996a

Deployment Tag:
None

Deployment Playbook Version:
Current

Deployment Contract Version:
June 22, 2026 → August 1, 2026

Architecture Version:
Economic State Architecture v1

Notes:

Last production commit:

1e45fab

Fix execution_agent to use ai_reasoning risk_level field.

Deployment Contract audit completed.

Items 1–7 verified.

---

# RUNTIME

Primary Entry Point:

master_runner.py

Runtime Coordinator:

master_runner.py

Service Manager:

systemd

Service Name:

morpho.service

Startup Method:

systemd service

Restart Policy:

Restart=always

Restart Delay:

5 seconds

Working Directory:

/root/morpho-agents

Python Interpreter:

/root/morpho-agents/venv/bin/python

Kill Switch:

Implemented

Validated

Persistent

Runtime Status:

Operational

Observed Stability:

10+ consecutive days

Expected Cycle:

Approximately 120 seconds

Current Runtime Health:

Healthy

---

# DATABASE

Database Type:

SQLite

Primary Operational Database:

trading_system.db

Database Location:

/root/morpho-agents/trading_system.db

Observed Size:

245 MB

Operational Source of Truth:

positions

Derived Operational Snapshot:

portfolio_state

Historical Tables:

executions

Backup Strategy:

Manual

Notes:

Database successfully migrated to Economic State Architecture.

positions is now the operational source of truth.

portfolio_state is derived from positions.

---

# CONFIGURATION

Environment File:

None

Wallet Configuration:

morpho_wallet.json

Telegram Configuration:

telegram_test.py

Secrets Storage:

Local production files

API Configuration:

Hyperliquid REST API

Configuration Status:

Validated

---
# OPERATIONAL STATE

Production Status:

Operational

Deployment Phase:

Pre-Deployment Evidence Phase

Evidence Phase Status:

ACTIVE

Capital Deployment:

No

Paper Trading:

Yes

Operational Health:

HEALTHY

Known Risks:

Telegram notifications may intermittently stop after several hours.

Operational engine remains unaffected.

Known Limitations:

No real capital deployed.

No automatic reconciliation.

Read-only exchange visibility only.

---

# PRODUCTION INVARIANTS

These conditions must always remain true.

□ positions is the operational Source of Truth.

□ portfolio_state is derived only from positions.

□ execution_agent prevents duplicate OPEN positions.

□ Kill Switch stops safe_runner execution.

□ Market prices originate only from market_data_manager.

□ Historical execution tables never become operational truth.

Violation of any invariant compromises production integrity.

---

# DEPLOYMENT CONTRACT STATUS

Item 1

positions.py Source of Truth

Status:

COMPLETED

Item 2

portfolio_state derived from positions

Status:

COMPLETED

Item 3

Duplicate prevention

Status:

COMPLETED

Item 4

Minimal Stop Loss

Status:

COMPLETED

Item 5

Basic Realized PnL

Status:

COMPLETED

Item 6

Kill Switch Validation

Status:

COMPLETED

Item 7

Read-Only Account Visibility

Status:

COMPLETED

Overall Status:

DEPLOYMENT CONTRACT COMPLETED

Deployment Ready:

YES

Pending:

Operational certification.

---

# OBSERVABILITY

Primary Logs:

systemd journal

journalctl -u morpho.service

Health Monitoring:

logger.py

runtime_state.json

Alerting:

Telegram

Runtime Verification:

systemctl status morpho.service

journalctl

Safe Runner health

Manual Verification:

Verify service.

Verify database.

Verify kill switch.

Verify runtime cycles.

Verify account visibility.


---

# RECOVERY

Rollback Procedure:

Restore latest verified Git commit.

Restore latest database backup if required.

Restart morpho.service.

Verify runtime health.

Recovery Time Objective (RTO):

Less than 30 minutes.

Recovery Point Objective (RPO):

Last verified backup.

Known Recovery Risks:

Database corruption.

Manual deployment errors.

Configuration drift.

Emergency Operator:

Daniel

---

# OPEN PRODUCTION ISSUES

PRD-001

Description:

Telegram notifications may stop after several hours while the production runtime continues operating normally.

Severity:

LOW

Impact:

Alerting only.

Core runtime unaffected.

Status:

Under observation.

Mitigation:

Manual verification through journalctl and systemd.

---

# DEPLOYMENT HISTORY

| Date | Commit | Description | Operator |
|------|--------|-------------|----------|
| 2026-06-26 | 1e45fab | Production deployment | Daniel |

---

# OPERATIONAL CHANGES

Record every production modification.

| Date | Change | Reason | Verified |
|------|--------|--------|----------|
| 2026-07-09 | Deployment Contract audit completed | Production certification | YES |

---

# OPERATIONAL INCIDENTS

| Date | Incident | Resolution | Lessons |
|------|----------|------------|---------|
| 2026-07 | Telegram alerts intermittently stop | Under observation | Runtime remained healthy |

---

# CURRENT PRODUCTION CHECKLIST

Before every deployment verify:

☑ Manifest matches production

☑ Commit verified

☑ Branch verified

☑ Runtime verified

☑ Database verified

☑ Backup verified

☑ Kill Switch verified

☑ Deployment Playbook reviewed

☑ Deployment Contract satisfied

☑ Runtime healthy

☑ Account visibility operational


---

# GOVERNANCE

This document is updated only after:

• Production deployment

• Infrastructure change

• Database migration

• Runtime architecture change

• Recovery event

• Major operational incident

Never update this document based on assumptions.

Only observed operational reality may modify this manifest.

---

# MORPHO OPERATIONAL PHILOSOPHY

Production is a living system.

Development evolves.

Production serves reality.

Documentation follows reality.

Reality never follows documentation.

Operational simplicity is preferred over architectural complexity.

Historical truth never replaces operational truth.

Derived state never becomes source truth.

Every production decision must remain observable, auditable and reversible.

Human governance always has final authority.

---

# PRODUCTION CERTIFICATION

Current Certification Status:

PRE-DEPLOYMENT CERTIFIED

Architecture Audit:

PASSED

Deployment Contract:

COMPLETED

Runtime Stability:

PASSED

Operational Database:

PASSED

Kill Switch:

PASSED

Account Visibility:

PASSED

Economic State Architecture:

PASSED

Remaining Requirement Before Real Capital:

Operational certification with live deployment authorization.

---

# NEXT PLANNED PHASE

Production Readiness

Objectives:

• Operational procedures

• Recovery drills

• Backup verification

• Secret management review

• Deployment certification

• Live capital authorization

No additional architecture work is authorized before Production Readiness is completed.

---

END OF DOCUMENT
