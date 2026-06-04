# MORPHO AGENTS — RUNBOOK

This document contains operational procedures for running, recovering, and maintaining Morpho infrastructure.

Its purpose is to reduce operational risk and preserve recovery procedures outside human memory.

---

# VPS ACCESS

## Connect to VPS

```bash id="xqv9z3"
ssh <user>@<server_ip>
```

## Navigate to project

```bash id="s8h2kp"
cd ~/morpho-agents
```

## Activate environment

```bash id="w4n7ty"
source venv/bin/activate
```

---

# SYSTEM STARTUP

## Standard startup flow

```bash id="p2m8rc"
python safe_runner.py
```

## Expected behavior

* runtime_state.json updates
* active modules execute
* governance checks occur before execution

---

# KILL SWITCH OPERATIONS

## Current Behavior

If:

```json id="9f7lqa"
"kill_switch_active": true
```

then:

```text id="m6t2yd"
safe_runner.py
```

will abort execution automatically.

---

# Verify kill switch state

```bash id="c1r8vx"
cat kill_switch_state.json
```

---

# HEALTH CHECKS

## Verify runtime state

```bash id="e5k9zn"
cat runtime_state.json
```

---

## Verify recent logs

```bash id="t3b7jw"
sqlite3 trading_system.db
```

Then:

```sql id="6j2mqs"
SELECT * FROM system_health
ORDER BY ROWID DESC
LIMIT 10;
```

---

# DATABASE BACKUP

## Manual backup

```bash id="u8v4ke"
cp trading_system.db trading_system_backup.db
```

---

# GIT OPERATIONS

## Pull latest version

```bash id="g4r9xp"
git pull
```

## Push changes

```bash id="b6y1nh"
git add .

git commit -m "update"

git push
```

---

# RECOVERY PROCEDURES

## If safe_runner.py fails

### Verify:

* runtime_state.json
* kill_switch_state.json
* SQLite integrity
* module errors
* VPS disk space
* active Python processes

---

## If database corruption is suspected

### Immediate actions

1. stop execution
2. backup current DB
3. inspect recent writes
4. restore latest clean backup if necessary

---

# IMPORTANT PRINCIPLES

* Never deploy major refactors directly to production runtime
* Prefer incremental migrations
* Validate governance systems before enabling execution
* Preserve backups before structural changes
* Operational stability is prioritized over rapid feature deployment

