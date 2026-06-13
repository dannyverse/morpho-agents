# VALIDATED INFRASTRUCTURE DIRECTIONS

## Centralized Market Data Layer

Discovered during realistic pricing migration.

Current architecture performs repeated HTTP requests per asset position:

position
→ requests.post()
→ full Hyperliquid mids snapshot
→ extract single asset
→ repeat again

This creates:

* request fanout
* sequential latency
* runtime slowdown
* inefficient market state ownership

Validated future direction:

single request
→ shared market snapshot
→ local cache
→ reusable get_price(asset)

Target future module:

market_data_manager.py

Minimal intended responsibilities:

* refresh_market_data()
* get_price(asset)
* last_price_update_timestamp

Important:
keep implementation operationally simple.
Avoid:

* websocket complexity
* async daemons
* distributed infra
* event buses

Goal:
single-owner market state architecture aligned with Morpho operational simplicity philosophy.

---

## Economic State Freshness Tracking

Future observability improvement:

Track:

* last market snapshot update
* stale pricing conditions
* degraded economic state freshness

Potential future fields:

* last_price_update_timestamp
* market_data_age_seconds
* stale_market_data flag

Purpose:
improve auditability and runtime governance visibility.

---

## Future Economic Infrastructure Layer

Validated future evolution path:

governed infrastructure
→ opportunity intelligence
→ economic execution persistence
→ centralized economic state management

Current remaining debt is primarily:

* infrastructure scaling
* market data efficiency
* economic realism refinement

NOT structural corruption.
