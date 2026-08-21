# G27 — `aumentar bateria a LiPo 6S 10000mAh` → `battery_capacity_wh=6.0`

**Date:** 2026-08-21  
**Severity:** 🔴 product / parse  
**Status:** OPEN — Engineer CLI full-project walk  
**Project:** `autonomia-5540bda0ac16`

## Observed

```text
User > aumentar bateria a LiPo 6S 10000mAh

Jarvis > Parámetros aplicados: battery_capacity_wh=6.0
         autonomía: 2.5 min → 0.2 min
```

Parsed the **`6` from `6S`** as watt-hours instead of chemistry/cell-count + capacity.

## Expected

Either:
- bind/update battery to ~222 Wh (`lipo_6s_10000mah` seed), or
- refuse / ask clarification — **never** silently set 6 Wh

## Impact

Silent energy cliff; Continuity still suggests “aumentar payload”.

---

**End of finding.**
