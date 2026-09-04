# Implementation Review — CLI fail-routing coherence

**Date:** 2026-09-03  
**Reviewer:** JES / Cursor  
**IC:** [implementation_contract_cli_fail_routing_coherence.md](implementation_contract_cli_fail_routing_coherence.md)  
**Report:** [implementation_report_cli_fail_routing_coherence.md](implementation_report_cli_fail_routing_coherence.md)

**Verdict:** **PASS WITH NOTES**

The walk's four locked failures are fixed with shared helpers, real-orchestrator
tests, and no D8 / catalog / ERF / `status_type` enum drift. One §2.3 call site
remains generic; it is not the walk loop and does not block closure.

---

## 1. Contract checks

| § | Requirement | Result |
|---|---|---|
| 2.1 | `frame_next_missing_datum` + shared question; locked size-class sentence | **Pass** — `project_closure.py:218-298`; size-class copy is verbatim |
| 2.2 | `still_missing` keeps frame when class still needed | **Pass** — `orchestrator.py:3335-3341`; save turn asks class, not arch-hint close |
| 2.3 | Brief + probe + `_component_prompt` + startup structure use helper | **Pass with N1** — Brief/probe/startup/component prompt wired; `_append_arch_progress_hint` **in-progress** still generic (see Notes) |
| 2.4 | Rank-2: PASS claim only when `can_fly is True`; two new locked sentences; no optimize CTA echo | **Pass** — `project_continuity.py:412-435`; `next_useful_why` = `GAP-SIM-NOT-PASS` for fail cases |
| 2.5 | No complete-branch optimize CTA on fail; hint may keep evidence without CTA | **Pass** — `orchestrator.py:4521-4529`, `3488-3495` |
| 2.6 | WARNING line gated on `not continuity.situation` | **Pass** — `main.py:241` |
| 2.7 | No motor-catalog reopen for D8-margin case | **Pass** — `_try_start_assisted_motor_help` untouched for that branch |
| 3 | Six mandatory scenarios (+ related unit) | **Pass** — 7/7 in `tests/test_cli_fail_routing_coherence.py` |
| 4 / 0 | Non-goals | **Pass** — no D8, no new enum, no ERF, no orchestrator split |

Re-ran: `test_cli_fail_routing_coherence.py` 7/7; adjacent regressions
(`test_project_continuity`, `test_fn021_session_hygiene`,
`test_cli_stale_energy_recalc`, `test_structure_a`,
`test_cli_feasibility_semantics`) green. Report claim **2150** accepted
(2143 + 7).

---

## 2. Notes (non-blocking)

### N1 — `_append_arch_progress_hint` in-progress still generic

IC §2.3 named this surface alongside `build_startup_context`. Startup now
asks the shared class question. The hint path still emits:

```text
Siguiente bloque: Estructura (frame) — en progreso, define los parámetros que faltan.
```

when structure is `in_progress` for a class gap (reproduced). The **walk loop**
is closed by §2.2 (`still_missing` + follow-up), so PVC 650g no longer takes
this path. Residual: completing another block while structure is already
class-missing can still append the generic hint. Prefer a small follow-up
hotfix only if a later walk hits it — not a reopen of this IC.

### N2 — `class_incompatible` question copy is new

IC locked only the `size_class` sentence. Claude's incompatibility prompt is
LEVEL A / no “cabe” and consistent with Continuity's Structure A wording.
Acceptable. Flagged in the report; no change required.

### N3 — fixture completion in `test_project_continuity.py`

`can_fly: True` added to `test_continuity_sim_fail_without_underspec_unchanged`.
Not a weakened assertion — completes a field every real simulation sets, so
the new §2.4 branch does not misfire. Acceptable.

---

## 3. Scope discipline

Only the files in IC §5 plus the one continuity fixture completion were used
for this behavior. Catalog / D8 / `MotorSuggestion` / `_derive_overall` /
simulator formulas / public `status_type` enum unchanged.

---

## 4. Closure

Investigation + IC for CLI fail-routing coherence are **implemented and
reviewed**. Catalog honesty (C-A1) remains queued, not opened.

Optional next: CLI walk on a fresh project; N1 hotfix only if the residual
hint surfaces again.
