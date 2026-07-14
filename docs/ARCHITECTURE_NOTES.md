# Architecture Notes

## Historical Truth vs Operational Truth

Date: 2026-07-14

### Incident

opportunity_monitor loaded the complete signal_memory history
(>336,000 rows) although it only needed the latest state of each
active asset.

This produced:

- SQL: ~4.3s
- Processing: ~58s
- Total module: ~64s

### Root Cause

The module was consuming historical data instead of operational state.

Each asset existed thousands of times in signal_memory.
The algorithm iterated every historical record although only the
latest record per asset was required.

### Solution

Replace:

SELECT ...
FROM signal_memory
WHERE ...

with a query that retrieves only the latest row for each asset
using MAX(rowid).

### Result

Rows processed:

336,140
↓

46

Opportunity Monitor:

~64s
↓

~2s

Safe Runner:

~120s
↓

~57s

### Engineering Rule

Operational modules must consume operational state.

Historical tables are for analytics, not runtime execution.
