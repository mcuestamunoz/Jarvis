# Implementation Contract — FN-016 vs RETURN_HOME wizard precedence (`B1-fn016-rtl-wizard-precedence`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.23`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review **PASS WITH NOTES**. Tag **`v0.6.23`**.  
**Parents:**
- [DC ★ CLOSED](design_contract_fn016_rtl_wizard_precedence_b0.md)
- [FN-016 cycle close ★](cycle_close_fn016.md)
- T10 RETURN_HOME ★ @ **`v0.6.18`** · tip **`v0.6.21`** (+ T14 IC may land first — rebase as needed)

**Type:** Orchestrator precedence fix — acquisition FN-016 cancel beats RETURN_HOME intercept for overlapping phrases.  
**Opens:** **`0.6.23` / `v0.6.23`** on ACCEPT.  
**Cola:** **T15**

**Not:** remove RTL phrases · global ESCAPE_WORDS expand · tip-pin cleanup · ESC fence Buy · allow-list widen · CHARGE · copper.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-fn016-rtl-wizard-precedence`** |
| 2 | In `JarvisOrchestrator._handle_global_commands`, **before** vehicle Task intercepts (at minimum before RETURN_HOME): if `session.mode == DEFINE_MISSING_PARAMETERS` and `is_navigation_back_phrase(stripped)` → clear session + return `{status: cancelled, action: define_missing_params, message: …}` matching the existing DEFINE_MISSING FN-016 message |
| 3 | Leave `VEHICLE_RETURN_HOME_PHRASES` membership (`volver`/`vuelve` stay). Leave `NAVIGATION_BACK_WORDS` unchanged |
| 4 | IDLE / no wizard: `volver` still → `vehicle_return_home` via existing T10 path |
| 5 | Tests: green `test_fn016_navigation_parse_safety.py::test_volver_cancels_numeric_wizard_phase_b`; add T-pair asserting IDLE `volver` still RETURN_HOME; cover `vuelve` + `atras` mid-wizard cancel |
| 6 | Version **`0.6.23`**; PRIORIDAD/docs note; bump Buy-owned `0.6.22` checkpoints if T14 already landed on the tip |
| 7 | Out: ESC fence · tip pins · allow-list · CHARGE · copper |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` | early FN-016 cancel in `_handle_global_commands` when DEFINE_MISSING |
| `tests/test_fn016_navigation_parse_safety.py` | strengthen / add IDLE vs wizard precedence cases |
| `pyproject.toml` | `0.6.23` |
| Docs / PRIORIDAD | short note |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | DEFINE_MISSING + `volver` → `cancelled` / `define_missing_params`; session IDLE; no `vehicle_return_home` |
| T2 | DEFINE_MISSING + `vuelve` / `atras` → same cancel |
| T3 | IDLE + `volver` → `vehicle_return_home` (disarmed reject OK) |
| T4 | DEFINE_MISSING + numeric still accepted (existing Phase B numeric regression stays green) |
| T5 | `pyproject` `0.6.23` |

---

## 3. Acceptance

- [x] Wizard navigation-back beats RETURN_HOME intercept  
- [x] IDLE RTL phrases unchanged  
- [x] FN-016 suite green · T1–T5 · `0.6.23`  
- [x] Cursor review (**PASS WITH NOTES**) · [x] Engineer ACCEPT · tag **`v0.6.23`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-fn016-rtl-wizard-precedence (T15)

IC: .jes/artifacts/implementation_contract_fn016_rtl_wizard_precedence_b1.md
DC: .jes/artifacts/design_contract_fn016_rtl_wizard_precedence_b0.md (★ CLOSED)
Parent: FN-016 ★ closed; regression from T10 RETURN_HOME phrase overlap

In _handle_global_commands, BEFORE vehicle RETURN_HOME (and other vehicle)
intercepts: if session.mode == DEFINE_MISSING_PARAMETERS and
is_navigation_back_phrase(user_input) → cancel wizard with the same
status/action/message as the existing DEFINE_MISSING FN-016 block.
Do NOT remove volver/vuelve from VEHICLE_RETURN_HOME_PHRASES.
IDLE volver must still fulfill vehicle_return_home.
Keep ParamDefinitionSession + DEFINE_MISSING-branch FN-016 as defense.
Tests T1–T5. Bump to 0.6.23. Docs + PRIORIDAD. Report.
No ACCEPT claim. ESC fence / tip-pin cleanup / allow-list / CHARGE out.
```
