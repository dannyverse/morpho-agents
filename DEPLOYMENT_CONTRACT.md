# DEPLOYMENT CONTRACT

June 22, 2026 → August 1, 2026

---

# DEPLOYMENT TARGET

Target:

August 1, 2026

Status:

ACTIVE

Scope is frozen.

No silent postponements.

Any date change requires explicit written justification.

---

# ALLOWED WORK

Only these six items may be implemented.

1.

positions.py becomes Source of Truth

2.

portfolio_state becomes a derived snapshot from positions

3.

Duplicate prevention in execution_agent

4.

Minimal stop loss support

5.

Basic realized PnL on close

6.

Kill switch validation

---

# FORBIDDEN BEFORE DEPLOY

NO lifecycle engine

NO outcome engine

NO economic memory

NO meta intelligence improvements

NO new domains

NO additional agents

NO abstractions for future opportunity types

NO "while we're here"

---

# SESSION TEMPLATE

SCOPE CHECK

This session works exclusively on:

[ item number ]

Primary objective:

---

If a new discovery appears:

1. Document it.

2. Add it to FUTURE_IDEAS.md.

3. Do not implement it.

4. Finish the session.

5. Review after deployment.

---

# RULE

Discovery is not authorization.

Evidence is not authorization.

Interesting architecture is not authorization.

A real problem may be documented without being solved immediately.

No new discoveries are allowed to change scope automatically.

Scope changes require explicit written decisions.

---

# AUGUST 1 DECISION RULE

If August 1st, 2026 arrives and one or more of the six deployment items remain incomplete:

Deployment does not happen automatically.

Deployment does not postpone automatically.

Within 48 hours, an explicit written decision must be made.

OPTION A

Deploy with the completed items and explicitly accept the risks associated with the remaining incomplete items.

The missing items and accepted risks must be documented.

OPTION B

Set a new deployment date.

The reason for postponement must be documented.

The remaining scope must be explicitly defined.

No new scope may be added automatically.

No "while we're here" additions are allowed.

Silence is not a decision.

Incomplete work is not automatic justification for postponement.

A deadline is not automatic justification for deployment.

Both deployment and delay require conscious written decisions.
# ITEM 7

READ-ONLY ACCOUNT VISIBILITY

PURPOSE

Observe exchange account reality before real-capital deployment.

SCOPE

Implement read-only visibility for:

* Account balance
* Open positions
* Open orders

using Hyperliquid account endpoints.

ALLOWED

* Query clearinghouseState
* Query openOrders
* Display results
* Log results
* Generate alerts

FORBIDDEN

* Reconciliation Engine
* Automatic discrepancy resolution
* Automatic database modification
* Automatic position correction
* Automatic order cancellation
* Trading decisions based on discrepancies
* Any write operation to exchange
* Any signing operation
* Any use of private keys

RULE

If exchange reality differs from database reality:

Observe.

Log.

Alert.

Do not resolve.

Human interpretation remains mandatory during the Pre-Deployment Evidence Phase.

SUCCESS CRITERIA

Morpho can display:

* Account balance
* Open positions
* Open orders

from a wallet address using read-only exchange queries.

Nothing more.

