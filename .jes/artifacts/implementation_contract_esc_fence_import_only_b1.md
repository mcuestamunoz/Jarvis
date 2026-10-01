# Implementation Contract — ESC boundary fence import-only (`B1-esc-fence-import-only`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.24`**

**Status:** **Implemented** (Claude Code) — Cursor review **PASS WITH NOTES** → await Engineer ★ ACCEPT → tag **`v0.6.24`**.  
**Parents:**
- [DC ★ CLOSED](design_contract_esc_fence_import_only_b0.md)
- C10 ESC PWM stub ★ · T11 arm UX ★  
- Prefer land **after** T15 (`0.6.23`) so tip versions stay linear

**Type:** Test-fence honesty — AST/import-only scan for ESC symbols in `core`/`adapters`.  
**Opens:** **`0.6.24` / `v0.6.24`** on ACCEPT.  
**Cola:** **T16**

**Not:** ESC HAL changes · FN-016 · tip-pin mass cleanup · allow-list · CHARGE · copper · weakening the import ban.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-esc-fence-import-only`** |
| 2 | Rewrite `tests/test_fase_c_esc_pwm_stub_rung_b1.py::test_t9_esc_symbols_not_imported_by_orchestrator_or_craft_paths` to parse each `.py` with **AST** (or strip comments+docstrings first) and forbid only: import of `flight_control.esc` / module path containing it, and import/name binding / attribute use of `SimulatedEscSink` |
| 3 | Comment/docstring mentions of `SimulatedEscSink` **must not** fail the test |
| 4 | Add a negative control in the test file (or adjacent) proving a fake import would fail — keep isolation real |
| 5 | Optional: reword orchestrator arm-UX comment so it does not spell `SimulatedEscSink` — secondary |
| 6 | Version **`0.6.24`**; bump Buy-owned tip checkpoints |
| 7 | Out: FN-016 · tip pins · product ESC behavior changes |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `tests/test_fase_c_esc_pwm_stub_rung_b1.py` | AST/import-only fence + control |
| `src/jarvis/core/orchestrator.py` | optional comment hygiene only |
| `pyproject.toml` | `0.6.24` |
| Docs / PRIORIDAD | short note |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Current tree: `test_t9` green with honesty comment present |
| T2 | Injected temporary `from jarvis.flight_software.flight_control.esc import SimulatedEscSink` (test-local snippet / helper) would be detected — document via unit helper on sample source string |
| T3 | Sample source with only a comment `# SimulatedEscSink` does **not** fail the helper |
| T4 | `pyproject` `0.6.24` |

---

## 3. Acceptance

- [ ] Fence is import/use-only · prose allowed  
- [ ] Real import still forbidden · T1–T4 · `0.6.24`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.24`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-esc-fence-import-only (T16)

IC: .jes/artifacts/implementation_contract_esc_fence_import_only_b1.md
DC: .jes/artifacts/design_contract_esc_fence_import_only_b0.md (★ CLOSED)
Parent: C10 ESC stub ★; false positive from T11 arm-UX comment

Harden test_t9_esc_symbols_not_imported_by_orchestrator_or_craft_paths
to AST/import-only (ignore comments/docstrings). Keep ban on importing
flight_control.esc / SimulatedEscSink from jarvis.core and jarvis.adapters.
Add helper-level controls: comment-only source passes; real import fails.
Optional: reword orchestrator comment. No ESC HAL behavior change.
Bump to 0.6.24. Docs + PRIORIDAD. Report.
No ACCEPT claim. FN-016 / tip-pin cleanup / allow-list / CHARGE out.
Prefer land after T15 (0.6.23).
```
