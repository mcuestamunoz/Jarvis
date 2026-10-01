# Implementation Report — ESC boundary fence import-only (`B1-esc-fence-import-only`, T16)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_esc_fence_import_only_b1.md`](implementation_contract_esc_fence_import_only_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_esc_fence_import_only_b0.md) · C10 ESC PWM stub ★ · T11 arm UX ★ @ **`v0.6.19`** · landed after T15 (**`0.6.23`**)  
**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review PASS WITH NOTES.  
**Package / tag:** `0.6.24` / **`v0.6.24`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `tests/test_fase_c_esc_pwm_stub_rung_b1.py` | New `_esc_fence_violations(source)` helper — AST-only scan, forbids a real `flight_control.esc` module import and any real import/alias/name/attribute use of `SimulatedEscSink`; never inspects comments or string/docstring content. `test_t9_esc_symbols_not_imported_by_orchestrator_or_craft_paths` rewritten to use it. New `test_t9b_fence_helper_is_import_honest_not_substring` — negative controls (IC §2 T2/T3): comment-only and docstring-only mentions pass; a real import, an aliased-module + attribute-use import, and a bare submodule import all fail. New `test_pyproject_version_is_0_6_24` (T4) |
| `src/jarvis/core/orchestrator.py` | Optional hygiene (IC §0 row 5): reworded the T11 arm-UX comment to no longer spell the literal identifier `SimulatedEscSink` — same meaning, no behavior change |
| `pyproject.toml` | `0.6.24` |
| Buy-owned active-lineage version checkpoints (T0–T13/T15 Assistant/vehicle-task chain — **not** the parked Fase C 0.5.x pin, including this file's own `test_t11_pyproject_version_is_0_5_8`, left untouched) | bumped `0.6.23` → `0.6.24` in the 19 files this chain tracks |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD line + T16 row → "Implemented, await review" |

**Not touched:** ESC HAL behavior, `jarvis.core`/`jarvis.adapters` import boundary itself (still zero real imports of `flight_control.esc`/`SimulatedEscSink` — only the *test* that proves it got more honest), FN-016 (T15, already landed separately), T14 allow-list widen (still only authorized, not implemented).

---

## 2. Behavior

- The fence is now import/use-only: a comment or docstring may name `SimulatedEscSink` freely (exactly the T11 arm-UX case that was a false positive) without failing the suite.
- A real import — `from ...flight_control.esc import SimulatedEscSink`, an aliased-module import followed by `.SimulatedEscSink` attribute access, or even just importing the bare `esc` submodule — is still caught.
- Product invariant unchanged: `jarvis.core`/`jarvis.adapters` still contain zero real ESC craft coupling.

---

## 3. Tests executed

```text
pytest tests/test_fase_c_esc_pwm_stub_rung_b1.py -q -k 'not test_t11_pyproject_version'
→ 19 passed (file collects 20; parked historical tip-pin `test_t11_pyproject_version_is_0_5_8` left red by design)

pytest tests/ -q
→ 3881 passed, 9 skipped, 52 failed
```

The 52 failures are diffed byte-for-byte against this branch's pre-fix tip: **zero new failures**, and exactly one prior failure now fixed (`test_fase_c_esc_pwm_stub_rung_b1.py::test_t9_esc_symbols_not_imported_by_orchestrator_or_craft_paths`). The rest are the pre-existing, parked Fase C 0.5.x / early-0.6.x historical tip-pin debt — untouched, per DC §0 row 5 / Engineer's explicit "no tip-pin mass cleanup" direction.

---

## 4. Remaining

None for this Buy. T14 (allow-list widen) remains a separate, already-authorized IC — not implemented here.
