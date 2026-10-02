# Design Contract — ESC boundary fence import-only (`DC-esc-fence-import-only`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor  
**Status:** ★ **CLOSED** (Engineer 2026-10-01 — “los 2 tests son buys reales · lanza IC”)  
**Type:** Design lock — Fase C ESC isolation test must prove **imports/use**, not prose. False positive from T11 arm-UX comment mentioning `SimulatedEscSink`.  
**Parents:** [C10 ESC PWM stub ★](implementation_review_fase_c_esc_pwm_stub_rung_b1.md) · T11 arm UX ★ @ **`v0.6.19`** · **no new INV**

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Root cause: `test_t9_esc_symbols_not_imported_by_orchestrator_or_craft_paths` substring-scans whole `.py` files; orchestrator comment “Not SimulatedEscSink.arm()” trips the fence without any import/coupling |
| 2 | Fix shape: harden the fence to **AST import / attribute-use** only (or equivalent that ignores comments). Prose/docstrings may name `SimulatedEscSink` to deny coupling |
| 3 | Optional hygiene: reword the arm-UX comment to avoid the bare identifier — not sufficient alone; test must be import-honest |
| 4 | Keep the product invariant: `jarvis.core` / `jarvis.adapters` must not **import** `flight_control.esc` or `SimulatedEscSink` |
| 5 | Out: change ESC HAL · tip-pin cleanup · FN-016 Buy · allow-list widen · CHARGE · copper |
| 6 | Next code: IC **`B1-esc-fence-import-only`** (T16) → package **`0.6.24`** |

**Product sentence:** the ESC craft-coupling fence fails only on real imports/use, not on honesty comments.

**Why this Buy:** T11 added a correct denial comment; an over-broad string fence made the suite lie. Real test-debt Buy, separate from FN-016.
