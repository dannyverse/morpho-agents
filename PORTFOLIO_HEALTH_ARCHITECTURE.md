# PORTFOLIO HEALTH ARCHITECTURE — MORPHO AGENTS

## PURPOSE

Portfolio Health evaluates the structural and operational health of deployed capital.

It answers a single question:

"Is deployed capital operating under structurally healthy and resilient conditions?"

Portfolio Health focuses on structural fragility and deployment quality.

It does NOT evaluate:

* runtime integrity
* governance permissions
* strategy validity
* opportunity persistence
* market-wide danger

Those belong to separate architectural domains.

---

# DOMAIN SEPARATION

## Runtime State

Question:

"Is the machine operational?"

Owner:

runtime_monitor.py

---

## Risk State

Question:

"Are current market/system conditions dangerous?"

Future Owner:

risk_state_manager.py

---

## Governance State

Question:

"What operational actions are allowed?"

Owner:

kill_switch_manager.py

---

## Portfolio Health

Question:

"Is deployed capital structurally healthy and resilient?"

Future Owner:

portfolio_health_manager.py

---

## Opportunity Health (Future)

Question:

"Does this opportunity still possess valid edge?"

Planned Future Phase:

Phase 1+

---

# PORTFOLIO HEALTH RESPONSIBILITIES

Portfolio Health evaluates:

* concentration risk
* directional fragility
* protocol dependency
* chain dependency
* liquidity weakness
* deployment fragmentation
* inefficient capital structure
* leverage concentration
* exposure clustering
* unrealized drawdown concentration

The objective is to detect structural fragility before it becomes operational failure.

---

# SOURCE OF TRUTH RELATIONSHIP

Portfolio Health must derive operational information from:

position_state

position_state remains the operational Source Of Truth for deployed capital.

Portfolio Health should NOT derive operational state from:

* executions
* paper_portfolio
* historical telemetry

Historical data may support future analytics but must not become operational dependencies.

---

# PHASE 0 METRICS

## Core Metrics

### Capital Concentration

Maximum capital concentration in a single asset.

---

### Protocol Concentration

Maximum capital concentration in a single protocol.

---

### Chain Concentration

Maximum capital concentration in a single blockchain ecosystem.

---

### Directional Concentration

Directional imbalance:

LONG vs SHORT exposure.

---

### Position Fragmentation

Number of positions relative to portfolio size and average position quality.

---

### Deployment Efficiency

Relationship between:

* deployed capital
* idle capital
* operational allocation efficiency

---

### Unrealized Drawdown Concentration

Drawdown concentration across deployed positions.

---

### Leverage Concentration

Leverage dependency concentration.

---

### Exposure Clustering

Hidden concentration caused by correlated exposures.

---

### Liquidity Quality

Operational liquidity quality of deployed positions.

Initial implementation may use simplified heuristics.

---

# HEALTH SCORE

Portfolio Health should produce:

health_score

Range:

0-100

Purpose:

Provide a unified structural fragility assessment.

---

# PORTFOLIO HEALTH STATES

## HEALTHY

Portfolio structure considered operationally resilient.

---

## WARNING

Structural fragility beginning to increase.

Monitoring escalation recommended.

---

## UNSTABLE

Portfolio structure showing significant fragility.

Governance escalation may become necessary.

---

## CRITICAL

Portfolio structure considered dangerously fragile.

Governance escalation strongly recommended.

---

# INITIAL THRESHOLD PHILOSOPHY

Thresholds should initially be:

* simple
* conservative
* explainable
* manually adjustable

Threshold sophistication should evolve only after sufficient operational data exists.

Phase 0 prioritizes consistency over optimization.

---

# GOVERNANCE RELATIONSHIP

Portfolio Health should NOT directly manipulate runtime behavior.

If Portfolio Health detects critical structural conditions:

portfolio_health_manager.py
↓
kill_switch_manager.activate_kill_switch()
↓
governance persistence
↓
safe_runner enforcement

Governance ownership must remain centralized.

---

# STATE STRUCTURE DIRECTION

Future operational state:

portfolio_health_state.json

Expected structure:

```json
{
  "timestamp": "...",
  "health_score": 78,
  "status": "WARNING",
  "metrics": {},
  "alerts": [],
  "last_updated": "..."
}
```

---

# ARCHITECTURAL PRINCIPLES

Portfolio Health must remain:

* operationally focused
* structurally focused
* ownership-clean
* governance-aware
* independent from historical telemetry
* derived from operational state only

---

# FUTURE EVOLUTION

Potential future additions:

* regime-aware fragility analysis
* adaptive thresholds
* liquidity exit simulations
* cross-opportunity dependency analysis
* dynamic capital resilience scoring
* health trend analysis

These belong to future phases and should not complicate Phase 0 implementation.

---

# PHASE 0 PRIORITY

Phase 0 objective is NOT advanced portfolio intelligence.

Phase 0 objective is:

* ownership clarity
* structural visibility
* operational fragility detection
* governance integration
* clean architectural separation

