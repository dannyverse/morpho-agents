# MORPHO AGENTS — DEPLOYMENT PLAYBOOK

Version: 1.0

Status:
Operational Governance

Purpose:

This playbook defines the operational procedure for deploying Morpho safely into
production.

The Deployment Contract determines WHETHER deployment is authorized.

The Deployment Playbook determines HOW deployment is executed.

Both are mandatory.

---

# CORE PRINCIPLES

Reality before assumptions.

Observation before modification.

Backups before deployment.

Validation before execution.

Evidence before capital.

Rollback before troubleshooting.

Production is an operational system, not a development environment.

No production change without complete operational understanding.

No principle is above reality.

---

# PHASE 0 — REALITY VERIFICATION

Objective:

Understand production before touching production.

Verify:

□ Correct VPS

□ Correct project directory

□ Current branch

□ Current commit

□ Current production version

□ Active Python processes

□ Running services

□ Database location

□ Database size

□ Kill Switch status

□ Wallet configuration

□ Runtime status

Questions that must be answered:

What is currently running?

Who started it?

What keeps it running?

Which database is being used?

Is production healthy?

Can rollback be performed?

If any answer is unknown:

STOP.

Do not continue.

---

# PHASE 1 — PRODUCTION INVENTORY

Objective:

Create a complete snapshot of production.

Collect:

□ Project size

□ Database size

□ Database tables

□ Active processes

□ Environment variables

□ Python version

□ Installed dependencies

□ Existing backups

□ Logs

□ Runtime observations

Record:

Deployment date

Current version

Operational observations

Known risks

No changes are performed during this phase.

---

# PHASE 2 — BACKUP

Objective:

Guarantee recovery.

Create:

□ Project archive

□ Database backup

□ Configuration backup

Verify:

□ Backup exists

□ Backup readable

□ Backup size reasonable

□ Restore path documented

If backup verification fails:

STOP.

---

# PHASE 3 — FREEZE PRODUCTION

Objective:

Prevent state changes during deployment.

Actions:

Enable Kill Switch if required.

Stop execution.

Verify:

□ No safe_runner

□ No master_runner

□ No orphan Python processes

Production must be completely idle.

---

# PHASE 4 — CLEAN DEPLOYMENT

Objective:

Deploy a known version.

Actions:

Archive previous project.

Deploy new version.

Create clean virtual environment.

Install dependencies.

Restore configuration.

Never overwrite production blindly.

Never merge incompatible architectures.

Always deploy intentionally.

---

# PHASE 5 — CONFIGURATION VALIDATION

Verify:

□ Python version

□ Virtual environment

□ Requirements installed

□ Environment variables

□ Wallet configuration

□ API connectivity

□ Database connectivity

□ Permissions

Deployment does not continue until every validation succeeds.

---

# PHASE 6 — SMOKE TEST

Objective:

Validate infrastructure.

Execute:

□ account_visibility.py

□ safe_runner.py

□ Database access

□ Wallet visibility

□ Runtime initialization

No continuous execution.

No capital deployment.

---

# PHASE 7 — EVIDENCE PHASE

Objective:

Observe reality.

Validate:

□ Cycle execution

□ State ownership

□ Logging

□ Health monitoring

□ Governance

□ Database writes

□ Alerts

Collect evidence.

Do not introduce architectural changes unless reality demands them.

---

# PHASE 8 — GO LIVE

Production begins only if:

□ Deployment Contract satisfied

□ Smoke Test successful

□ Evidence Phase successful

□ Operational health acceptable

Enable production.

Monitor continuously.

---

# PHASE 9 — POST DEPLOYMENT VALIDATION

Verify:

□ Runtime stable

□ Expected modules active

□ Database behaving normally

□ Resource usage acceptable

□ Alerts functioning

□ No unexpected failures

Document observations.

---

# PHASE 10 — ROLLBACK

Rollback is governance.

Rollback is not failure.

If production becomes unsafe:

Stop execution.

Restore project backup.

Restore database.

Restore configuration.

Validate restoration.

Resume previous stable state.

Investigate only after stability has been restored.

---

# OPERATIONAL LESSONS

Every deployment must improve operational knowledge.

Unexpected discoveries must be documented.

Reality always overrides assumptions.

Production and development must never diverge unknowingly.

Operational understanding is part of deployment success.

---

# MORPHO DEPLOYMENT PHILOSOPHY

Development produces software.

Deployment produces operational reality.

Operational reality is always the final authority.
