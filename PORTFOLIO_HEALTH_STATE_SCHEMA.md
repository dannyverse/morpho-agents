# PORTFOLIO HEALTH STATE SCHEMA — PHASE 0

## PURPOSE

This document defines the operational schema for:

portfolio_health_state.json

The objective of this schema is to provide:

* structural visibility
* operational fragility assessment
* governance recommendations
* machine-readable portfolio health state

This is a derived operational state.

It is NOT a Source Of Truth.

---

# SOURCE OF TRUTH RELATIONSHIP

Portfolio Health derives operational information from:

position_state

Operational flow:

position_state
↓
portfolio_health_manager.py
↓
portfolio_health_state.json
↓
governance / dashboards / alerting

---

# SCHEMA VERSIONING

Portfolio Health schemas must include:

schema_version

This allows:

* safe schema evolution
* historical interpretation
* backward compatibility
* debugging
* migration safety

---

# PHASE 0 OPERATIONAL SCHEMA

```json id="jlwm2m"
{
  "schema_version": "1.0",

  "timestamp": "2026-06-05T15:42:11.123Z",

  "cycle_id": "20260605_154211_8f3a9c2d",

  "health_score": 78,

  "status": "WARNING",

  "metrics": {

    "max_asset_concentration": 45,

    "max_protocol_concentration": 62,

    "max_chain_concentration": 81,

    "directional_bias": 90,

    "position_count": 18,

    "position_fragmentation_score": 35,

    "deployment_efficiency": 72,

    "global_unrealized_drawdown_pct": -4.8,

    "drawdown_concentration": 18,

    "leverage_concentration": 40,

    "exposure_clustering": 67,

    "liquidity_risk_score": 74
  },

  "triggered_thresholds": [

    {
      "metric": "directional_bias",

      "value": 90,

      "threshold": 75,

      "severity": "WARNING"
    },

    {
      "metric": "max_chain_concentration",

      "value": 81,

      "threshold": 70,

      "severity": "WARNING"
    }
  ],

  "alerts": [

    "High chain concentration detected",

    "Directional imbalance elevated"
  ],

  "governance_signal": {

    "requires_attention": true,

    "recommended_action": "MONITOR",

    "escalation_level": "WARNING"
  },

  "derived_from": "position_state",

  "calculation_version": "0.9",

  "last_updated": "2026-06-05T15:42:11.123Z"
}
```

---

# HEALTH STATES

Portfolio Health states:

* HEALTHY
* WARNING
* UNSTABLE
* CRITICAL

Purpose:

Provide operational structural fragility classification.

---

# GOVERNANCE ACTION ENUMS

Valid governance recommendations:

* MONITOR
* REDUCE_EXPOSURE
* HALT_NEW_POSITIONS
* ESCALATE_TO_KILL_SWITCH

Portfolio Health provides recommendations only.

Governance remains centralized through:

kill_switch_manager.py

---

# TRIGGERED THRESHOLDS

triggered_thresholds exists to provide:

* machine-readable escalation context
* programmatic alerting support
* governance processing support
* dashboard integration
* future analytics compatibility

alerts remain human-readable summaries.

---

# PHASE 0 THRESHOLD PHILOSOPHY

Thresholds should initially be:

* simple
* conservative
* explainable
* manually adjustable

Phase 0 prioritizes:

consistency

>

optimization

Threshold sophistication belongs to later phases after sufficient operational data exists.

---

# PHASE 0 DESIGN CONSTRAINTS

Phase 0 intentionally excludes:

* adaptive thresholds
* trend analysis
* regime awareness
* predictive fragility models
* opportunity persistence analysis
* historical intelligence layers

The objective is operational clarity, not advanced portfolio intelligence.

---

# FUTURE OWNER

portfolio_health_manager.py

Responsibilities:

* read position_state
* calculate portfolio fragility metrics
* generate health_score
* generate governance recommendations
* write portfolio_health_state.json

---

# ARCHITECTURAL ROLE

Portfolio Health represents:

Derived Operational Structural Intelligence

It is not:

* runtime state
* governance state
* opportunity intelligence
* execution state

Its purpose is to evaluate structural fragility of deployed capital.


